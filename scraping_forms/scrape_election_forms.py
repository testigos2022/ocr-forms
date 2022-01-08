from dataclasses import dataclass

from bs4 import BeautifulSoup

from scraping_forms.nested_dropdowns import NestedDropDowns
from scraping_forms.selenium_util import click_it


@dataclass
class ESCCong(NestedDropDowns):
    def get_pdf_urls(self):
        submit_button = "/html/body/div/div[2]/div[3]/div/div[1]/div/form/a"
        click_it(self.wd, submit_button)
        # self.wd.save_screenshot(f"screenshot.png")
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
