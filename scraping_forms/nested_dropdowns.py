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
from typing import Optional, List

from beartype import beartype
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from scraping_forms.beartypes import NeList
from scraping_forms.readwrite_files import read_json, write_json, write_jsonl
from selenium_scraping.selenium_util import ChromeDriver, retry


@beartype
def get_options(wd: WebDriver, xpath: str) -> NeList:
    element: WebElement = wd.find_element(by=By.XPATH, value=xpath)
    element.click()
    sleep(0.1)
    options = element.find_elements_by_tag_name("option")
    return options


@dataclass
class DropDownSelection:
    name: str
    xpath: str
    stop: Optional[int] = None
    start_option: Optional[str] = None


@beartype
def get_click_option(
    wd: WebDriver, sel: DropDownSelection, option: str, blacklist: list[str]
):
    option_elements = get_options(wd, sel.xpath)
    options_texts = [e.text for e in option_elements]
    # print(f"{sel.name=} searching for {option} in {options_texts}")
    failed = True
    sleep(0.3)
    for e, ot in zip(option_elements, options_texts):
        if ot == option:
            e.click()
            e.click()
            failed = False
            break
    else:
        print(f"could not find {option=} in {options_texts} of {sel.name}")
    options_texts = [o for o in options_texts if o not in blacklist]
    return failed, options_texts


@beartype
def _calc_start(options: NeList[str], sel: DropDownSelection):
    if sel.start_option is not None:
        if sel.start_option in options:
            start = options.index(sel.start_option)
        else:
            print(f"could not find {sel.start_option=} in {options=} -> starting at 0!")
            # start=int(input("enter start:"))
            start = 0
        sel.start_option = None  # so that next time it starts at 1
    else:
        start = 0
    return start


@beartype
def get_options_and_start(
    wd: WebDriver, sel: DropDownSelection, option_blacklist: list[str]
) -> tuple[list[str], int]:
    options = [
        o.text for o in get_options(wd, sel.xpath) if o.text not in option_blacklist
    ]
    assert len(options) > 0

    if len(options) > 0:
        start = _calc_start(options, sel)
    else:
        start = 0
    return options, start


@dataclass
class NestedDropDowns:
    base_url: str
    url: str
    download_path: str
    data_dir: str
    selections: NeList[DropDownSelection]
    option_blacklist: List[str] = field(default_factory=lambda: ["SELECCIONE"])
    before_pdfs_wait: float = 0.5
    between_two_pdfs_wait_time: float = 1.0  # seconds
    headless: bool = True
    state: Optional[dict] = None

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
        fail_count = 0
        while True:
            if self.state is None and os.path.isfile(self.state_json):
                self.state = read_json(self.state_json)
            try:
                with ChromeDriver(self.download_path, headless=self.headless) as wd:
                    self._run(wd)
                os.remove(self.state_json)
                self.state = None
                for opt in self.selections:
                    opt.start_option = None
                    opt.stop = None
            except BaseException as e:
                fail_count += 1
                print(f"run failed with: {e}")
                if fail_count <= 1:
                    write_json(self.state_json, self.state)
                    print(f"wrote state: {self.state}")
                    traceback.print_exc()
                else:
                    print("wipe state")
                    fail_count = 0
                    os.remove(self.state_json)
                    self.state = None
                    for opt in self.selections:
                        opt.start_option = None
                        opt.stop = None
                sleep(3.0)

    @beartype
    def _run(self, wd: WebDriver):
        self._set_start_state()
        self.to_be_moved = {}
        self.wd = wd
        self.wd.get(self.url)
        self._recurse_through_dropdown_tree(self.selections, selection_path=[])

    @abstractmethod
    def get_pdf_urls(self) -> List[str]:
        raise NotImplemented

    @beartype
    def _recurse_through_dropdown_tree(
        self, selections: List[DropDownSelection], selection_path: List[str]
    ):
        sys.stdout.write(f"\r{selection_path=}")
        sel = selections[0]
        step_in_selection_wait = 1.0
        sleep(step_in_selection_wait)

        options, start = retry(
            lambda: get_options_and_start(self.wd, sel, self.option_blacklist),
            wait_time=0.5,
            num_retries=4,
            increase_wait_time=True,
            do_raise=False,
            default=([], 0),
            fail_message="failed to get options",
        )
        stop = len(options) if sel.stop is None else sel.stop
        todo_options = [options[k] for k in range(start, stop)]
        done_options = []
        while len(todo_options) > 0:
            option = todo_options[0]
            try:
                for _ in range(1):
                    failed, options = retry(
                        lambda: get_click_option(
                            self.wd, sel, option, self.option_blacklist
                        ),
                        wait_time=0.5,
                        num_retries=3,
                        increase_wait_time=True,
                        fail_message="failed to get+click option",
                        do_raise=True,
                    )
                if failed:
                    todo_options = [o for o in options if o not in done_options]
                else:
                    todo_options.pop(todo_options.index(option))
                    done_options.append(option)
                    selection_path.append(option)

                    is_last = len(selections) == 1
                    if not is_last:
                        retry(
                            lambda: self._recurse_through_dropdown_tree(
                                selections[1:], selection_path
                            ),
                            fail_message="recurse-retry failed!",
                        )
                    else:
                        self._process_selection_leaf(selection_path)
                        self._process_selection_leaf(selection_path)
            except Exception as e:
                print(f"FAILED to recurse at: {selection_path} with: {e}")
                raise e
            finally:
                self._move_files()
                if option in selection_path:
                    pop_index = selection_path.index(option)
                    selection_path.pop(pop_index)

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

    @beartype
    def _process_selection_leaf(self, selection_path: NeList[str]):
        sys.stdout.write(f"\r{selection_path=}")
        sleep(self.before_pdfs_wait)
        num_pdfs = 0
        num_pdfs_downloaded = 0
        selection_path_copy = selection_path.copy()
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
                    write_jsonl(
                        f"{self.download_path}/selection_states.jsonl",
                        [
                            {
                                "selection_path": selection_path,
                                "pdf_file": pdf_file,
                                "pdf_file_full": pdf_file_full,
                                "pdf_url": pdf_url,
                            }
                        ],
                        mode="ab",
                    )
                    sleep(self.between_two_pdfs_wait_time)
                else:
                    sys.stdout.write(f"\ralready got {pdf_file}")

        finally:
            write_jsonl(
                f"{self.download_path}/selection_states.jsonl",
                [
                    {
                        "selection_path": selection_path,
                        "num_pdfs": num_pdfs,
                        "num_pdfs_downloaded": num_pdfs_downloaded,
                    }
                ],
                mode="ab",
            )
