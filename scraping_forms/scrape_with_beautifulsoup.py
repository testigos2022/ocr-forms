import os
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from data_io.download_extract_files import wget_file
from data_io.readwrite_files import write_lines, read_lines
from misc_utils.cached_data import CachedData, ContinuedCachedData
from misc_utils.dataclass_utils import _UNDEFINED, UNDEFINED


@dataclass
class WgetPdfs(ContinuedCachedData):
    url: Union[_UNDEFINED, str] = UNDEFINED
    name: Union[_UNDEFINED, str] = UNDEFINED

    def continued_build_cache(self) -> None:
        pdf_dir = self.prefix_cache_dir("pdfs")

        if not os.path.isfile(self.hrefs_file):
            self._write_hrefs_file()
            os.makedirs(pdf_dir)

        already_downloaded = list(Path(pdf_dir).glob("*.*"))
        hrefs = [s for s in read_lines(self.hrefs_file) if s not in already_downloaded]
        print(f"already got: {len(already_downloaded)}, {len(hrefs)} still TODO")
        for pdf_file in tqdm(hrefs, desc="wgetting pdfs-files"):
            wget_file(f"{url}/{pdf_file}", pdf_dir)

    def _write_hrefs_file(self):
        page = requests.get(self.url)
        soup = BeautifulSoup(page.text, features="html.parser")
        all_hrefs = list(set([x.attrs["href"] for x in soup.find_all("a")]))

        def is_pdf(s: str):
            return any((s.endswith(suffix) for suffix in ["pdf", "PDF", "Pdf"]))

        hrefs = list(set([x for x in all_hrefs if is_pdf(x)]))
        nonpdf_hrefs = list(set([x for x in all_hrefs if not is_pdf(x)]))
        print(f"{len(hrefs)} of {len(all_hrefs)} are pdfs")
        print(f"non-pdf hrefs: {nonpdf_hrefs}")
        write_lines(self.hrefs_file, hrefs)

    @property
    def hrefs_file(self):
        return self.prefix_cache_dir(f"hrefs.txt")


if __name__ == "__main__":
    url = "https://elecciones1.registraduria.gov.co/esc_cong_2018/archivos/divulgacion/"
    WgetPdfs(url=url, cache_base=os.environ["DATA_PATH"], name="esc_cong_2018").build()
