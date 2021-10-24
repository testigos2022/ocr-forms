import gzip
import json
import os
import shutil
import sys
import traceback

from abc import abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from time import sleep
from typing import List, Tuple, Optional

from bs4 import BeautifulSoup
from selenium.webdriver.remote.webelement import WebElement
from tqdm import tqdm
from util import data_io
from util.data_io import read_json, write_json

from selenium_util import click_it, ChromeDriver, retry


def get_options(wd, xpath):
    element: WebElement = wd.find_element_by_xpath(xpath)
    element.click()
    options = element.find_elements_by_tag_name("option")
    return options


@dataclass
class DropDownSelection:
    name: str
    xpath: str
    stop: Optional[int] = None
    start_option: Optional[str] = None


@dataclass
class NestedDropDowns:
    base_url: str
    url: str
    download_path: str
    data_dir: str
    selections: List[DropDownSelection]
    option_blacklist: List[str] = field(default_factory=lambda: ["SELECCIONE"])
    between_two_pdfs_wait_time: float = 1.0  # seconds
    headless: bool = True
    state: Optional = None

    @property
    def state_json(self):
        return f"{self.download_path}/state.json"

    def _set_start_state(self):
        os.makedirs(self.download_path, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        # if last_states is None or len(last_states)==0:
        #     last_states = [
        #         d["selection_path"]
        #         for d in data_io.read_jsonl(f"{self.download_path}/selection_states.jsonl")
        #     ][-1]
        if self.state is not None:
            print(f"start-state:{self.state}")
            for option, selection in zip(self.state["selection_path"], self.selections):
                if option not in self.option_blacklist:
                    selection.start_option = option

        return self

    def run(self):
        if os.path.isfile(self.state_json):

            def read_json(file: str, mode="b"):
                with gzip.open(file, mode="r" + mode) if file.endswith("gz") else open(
                    file, mode="r" + mode
                ) as f:
                    s = f.read()
                    s = s.decode("utf-8") if mode == "b" else s
                    s = s.replace("'", '"')
                    return json.loads(s)

            self.state = read_json(self.state_json)

        while True:
            try:
                with ChromeDriver(self.download_path, headless=self.headless) as wd:
                    self._run(wd)
            except BaseException as e:
                write_json(self.state_json, self.state)
                print(f"run failed with: {e}")
                print(f"wrote state: {self.state}")
                traceback.print_exc()
                sleep(3.0)

    def _run(self, wd):
        self.selection_path = []
        self._set_start_state()
        self.to_be_moved = {}
        self.wd = wd
        self.wd.get(self.url)
        self._recurse_through_dropdown_tree(self.selections)

    @abstractmethod
    def get_pdf_urls(self) -> List[str]:
        raise NotImplemented

    def _click_option(self, xpath: str, option: str):
        option_elements = retry(
            lambda: get_options(self.wd, xpath),
            wait_time=0.1,
            increase_wait_time=True,
            fail_message="failed to get options",
        )
        for e in option_elements:
            if e.text == option:
                e.click()
                break
        else:
            raise Exception(f"could not click {option=}")

    def _recurse_through_dropdown_tree(
        self,
        selections: List[DropDownSelection],
    ):
        sel = selections[0]
        step_in_selection_wait = 0.1
        sleep(step_in_selection_wait)

        option_elements = retry(
            lambda: get_options(self.wd, sel.xpath),
            wait_time=0.1,
            increase_wait_time=True,
            fail_message="failed to get options",
        )
        options = [o.text for o in option_elements]
        start = self._calc_start(options, sel)
        stop = len(options) if sel.stop is None else sel.stop
        for k in range(start, stop):
            option = options[k]
            try:
                self._click_option(sel.xpath, option)
                if option in self.option_blacklist:
                    continue
                self.selection_path.append(option)
                is_last = len(selections) == 1
                if not is_last:
                    self._recurse_through_dropdown_tree(selections[1:])
                else:
                    self._process_selection_leaf()
            finally:
                self._move_files()
                if option in self.selection_path:
                    sys.stdout.write(f"\r{self.selection_path=},{option=}")
                    pop_index = self.selection_path.index(option)
                    self.selection_path.pop(pop_index)

    def _calc_start(self, options: List[str], sel):

        if sel.start_option is not None:
            if sel.start_option in options:
                start = options.index(sel.start_option)
            else:
                print(
                    f"could not find {sel.start_option=} in {options=} -> starting at 0!"
                )
                start = 0
            sel.start_option = None  # so that next time it starts at 1
        else:
            start = 0
        return start

    def _move_files(self):
        for f in Path(self.download_path).glob("*.pdf"):
            if f.name not in self.to_be_moved.keys():
                # print(f"{f.name} is not in {self.to_be_moved.keys()}")
                continue
            dest = self.to_be_moved.pop(f.name)
            shutil.move(
                f"{str(f)}",
                f"{self.data_dir}/{dest}",
            )

        def already_moved(file):
            return os.path.isfile(f"{self.data_dir}/{file}")

        # print(f"{len(self.to_be_moved)=}")
        self.to_be_moved = {
            k: v for k, v in self.to_be_moved.items() if not already_moved(v)
        }
        # print(f"{len(self.to_be_moved)=} cleaned by already moved ones")

    def _process_selection_leaf(self):
        get_pdfs_wait = 0.1
        sleep(get_pdfs_wait)
        num_pdfs = 0
        num_pdfs_downloaded = 0
        assert len(self.selection_path) > 0
        selection_path_copy = [p for p in self.selection_path]
        self.state = {"selection_path": selection_path_copy}
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
                    sys.stdout.write(f"\ralready got {pdf_file}")

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
