import os
import shutil

from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from time import sleep
from typing import List, Tuple, Optional

from bs4 import BeautifulSoup
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm
from util import data_io

from selenium_util import click_it, build_chrome_driver


def get_options(wd, xpath):
    element: WebElement = wd.find_element_by_xpath(xpath)
    element.click()
    options = [e.text for e in element.find_elements_by_tag_name("option")]

    return options


@dataclass
class DropDownSelection:
    name: str
    xpath: str
    start: Optional[int] = None
    stop: Optional[int] = None
    start_option: Optional[str] = str


@dataclass
class NestedDropDowns:
    base_url: str
    url: str
    download_path: str
    data_dir: str
    selections: List[DropDownSelection]
    between_two_pdfs_wait_time: float = 1.0  # seconds
    headless: bool = True

    def init(self):
        os.makedirs(self.download_path, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

        last_states = [
            d["selection_path"]
            for d in data_io.read_jsonl(f"{self.download_path}/selection_states.jsonl")
        ][-1]
        print(f"{last_states=}")
        for option, selection in zip(last_states, self.selections):
            if selection.start is None:
                selection.start_option = option

        self.wd = build_chrome_driver(self.download_path, headless=self.headless)
        self.wd.get(self.url)
        return self

    def run(self):
        self.selection_path = []
        self.to_be_moved = {}

        self._recurse_through_dropdown_tree(self.selections)

    @abstractmethod
    def get_pdf_urls(self) -> List[str]:
        raise NotImplemented

    def _recurse_through_dropdown_tree(
        self,
        selections: List[DropDownSelection],
    ):
        sel = selections[0]
        sleep(1)
        options = get_options(self.wd, sel.xpath)

        if sel.start is None and sel.start_option is not None:
            start = None
            for k in range(3):
                try:
                    assert (
                        sel.start_option in options
                    ), f"{sel.start_option=} not in {options=}"
                    start = options.index(sel.start_option) + 1
                    sel.start_option = None
                    break
                except BaseException as e:
                    sleep(1.0)
                    options = get_options(self.wd, sel.xpath)
            if start is None:
                raise AssertionError

        elif sel.start is not None:
            start = sel.start
        else:
            start = 1

        num_options = len(options)
        stop = num_options if sel.stop is None else sel.stop
        for k in range(start, stop):
            option_xpath = f"{sel.xpath}/option[{k}]"
            selected_option = None
            try:
                element = self.wd.find_element_by_xpath(option_xpath)
                element.click()
                selected_option = element.text
                self.selection_path.append(selected_option)
                # print(f"{name=}, option: {self.wd.find_element_by_xpath(option_xpath).text}")
                sleep(1)
                is_last = len(selections) == 1
                if not is_last:
                    self._recurse_through_dropdown_tree(selections[1:])
                else:
                    self._process_selection_leaf()
            finally:
                self._move_files()
                if selected_option is not None:
                    print(f"{self.selection_path=},{selected_option=}")
                    pop_index = self.selection_path.index(selected_option)
                    self.selection_path.pop(pop_index)

    def _move_files(self):
        for f in tqdm(Path(self.download_path).glob("*.pdf"), desc="moving files"):
            if f.name not in self.to_be_moved.keys():
                print(f"{f.name} is not in {self.to_be_moved.keys()}")
                continue
            dest = self.to_be_moved.pop(f.name)
            shutil.move(
                f"{str(f)}",
                f"{self.data_dir}/{dest}",
            )

        def already_moved(file):
            return os.path.isfile(f"{self.data_dir}/{file}")

        print(f"{len(self.to_be_moved)=}")
        self.to_be_moved = {
            k: v for k, v in self.to_be_moved.items() if not already_moved(v)
        }
        print(f"{len(self.to_be_moved)=} cleaned by already moved ones")

    def _process_selection_leaf(self):
        sleep(1)
        num_pdfs = 0
        num_pdfs_downloaded = 0
        try:
            pdfs = self.get_pdf_urls()
            for pdf_url in pdfs:
                pdf_file_full = pdf_url.replace(f"{self.base_url}/", "").replace(
                    "/", "_"
                )
                pdf_file = pdf_url.split("/")[-1]
                self.to_be_moved[pdf_file] = pdf_file_full
                num_pdfs += 1
                download_in_process = os.path.isfile(
                    f"{self.download_path}/{pdf_file}.crdownload"
                )
                already_in_data_dir = os.path.isfile(f"{self.data_dir}/{pdf_file_full}")
                already_got_it = already_in_data_dir or download_in_process
                if not already_got_it:
                    self.wd.get(pdf_url)
                    num_pdfs_downloaded += 1
                    data_io.write_jsonl(
                        f"{self.download_path}/selection_states.jsonl",
                        [
                            {
                                "selection_path": self.selection_path,
                                "pdf_file": pdf_file,
                                "pdf_file_full": pdf_file_full,
                            }
                        ],
                        mode="ab",
                    )
                    sleep(self.between_two_pdfs_wait_time)
                else:
                    print(f"already got {pdf_file}")

        finally:
            data_io.write_jsonl(
                f"{self.download_path}/selection_states.jsonl",
                [
                    {
                        "selection_path": self.selection_path,
                        "num_pdfs": num_pdfs,
                        "num_pdfs_downloaded": num_pdfs_downloaded,
                    }
                ],
                mode="ab",
            )


@dataclass
class ESCCong(NestedDropDowns):
    def get_pdf_urls(self):
        submit_button = "/html/body/div/div[2]/div[3]/div/div[1]/div/form/a"
        # click_it(self.wd, submit_button)
        sleep(1)
        self.wd.save_screenshot(f"screenshot.png")
        soup = BeautifulSoup(self.wd.page_source, features="html.parser")
        pdfs = [
            f"{self.base_url}{e.attrs['href']}" for e in soup.find_all(class_="btnPdf")
        ]
        return pdfs


@dataclass
class E14Cong2018(NestedDropDowns):
    def get_pdf_urls(self):
        soup = BeautifulSoup(self.wd.page_source, features="html.parser")
        pdfs = [
            f"{e.attrs['href']}"
            for e in soup.find_all("a")
            if "javascript" not in e.attrs["href"]
        ]
        return pdfs
