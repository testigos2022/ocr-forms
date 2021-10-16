import os
import sys

sys.path.append(".")

from abc import abstractmethod
from dataclasses import dataclass
from time import sleep
from typing import List, Tuple, Optional

from bs4 import BeautifulSoup
from selenium.webdriver.remote.webelement import WebElement

from selenium_util import click_it, build_chrome_driver


def get_num_options(wd, name, xpath):
    element: WebElement = wd.find_element_by_xpath(xpath)
    element.click()
    options = [e.text for e in element.find_elements_by_tag_name("option")]
    num_options = len(options)
    print(f"{name}: {num_options=}, {options=}")
    return num_options


@dataclass
class DropDownSelection:
    name: str
    xpath: str
    start: int = 1
    stop: Optional[int] = None


@dataclass
class NestedDropDowns:
    base_url: str
    url: str
    download_path: str
    selections: List[DropDownSelection]
    between_two_pdfs_wait_time: float = 1.0  # seconds
    headless:bool=True

    def init(self):
        os.makedirs(self.download_path, exist_ok=True)
        self.wd = build_chrome_driver(self.download_path, headless=headless)
        self.wd.get(self.url)
        return self

    def run(self):
        self._recurse_through_dropdown_tree(self.selections)

    @abstractmethod
    def get_pdf_urls(self) -> List[str]:
        raise NotImplemented

    def _recurse_through_dropdown_tree(self, selections: List[DropDownSelection]):
        sel = selections[0]
        num_options = get_num_options(self.wd, sel.name, sel.xpath)
        stop = num_options if sel.stop is None else sel.stop
        for k in range(sel.start, stop):
            option_xpath = f"{sel.xpath}/option[{k}]"
            try:
                click_it(self.wd, option_xpath)
                # print(f"{name=}, option: {self.wd.find_element_by_xpath(option_xpath).text}")
                sleep(1)
                is_last = len(selections) == 1
                if not is_last:
                    self._recurse_through_dropdown_tree(selections[1:])
                else:
                    self._process_selection_leaf()
            except BaseException as e:
                print(e)

    def _process_selection_leaf(self):
        sleep(1)
        try:
            pdfs = self.get_pdf_urls()
            for pdf_url in pdfs:
                pdf_file = pdf_url.split("/")[-1]
                already_got_it = os.path.isfile(
                    f"{self.download_path}/{pdf_file}"
                ) or os.path.isfile(f"{self.download_path}/{pdf_file}.crdownload")
                if not already_got_it:
                    self.wd.get(pdf_url)
                    sleep(self.between_two_pdfs_wait_time)
                else:
                    print(f"already got {pdf_file}")

        except BaseException as e:
            print(e)


@dataclass
class ESCCong(NestedDropDowns):
    def get_pdf_urls(self):
        submit_button = "/html/body/div/div[2]/div[3]/div/div[1]/div/form/a"
        click_it(self.wd, submit_button)
        sleep(1)

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



