import os
from dataclasses import dataclass
from typing import Union

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from data_io.download_extract_files import wget_file
from data_io.readwrite_files import write_lines
from misc_utils.cached_data import CachedData
from misc_utils.dataclass_utils import _UNDEFINED, UNDEFINED


@dataclass
class WgetPdfs(CachedData):
    url: Union[_UNDEFINED, str] = UNDEFINED

    def _build_cache(self):
        page = requests.get(self.url)
        soup = BeautifulSoup(page.text, features="html.parser")
        all_hrefs = list(set([x.attrs["href"] for x in soup.find_all("a")]))

        def is_pdf(s: str):
            return any((s.endswith(suffix) for suffix in ["pdf", "PDF", "Pdf"]))

        hrefs = list(set([x for x in all_hrefs if is_pdf(x.attrs["href"])]))
        nonpdf_hrefs = list(set([x for x in all_hrefs if not is_pdf(x.attrs["href"])]))
        print(f"{len(hrefs)} of {len(all_hrefs)} are pdfs")
        print(f"non-pdf hrefs: {nonpdf_hrefs}")
        write_lines(self.prefix_cache_dir(f"hrefs.txt"), hrefs)

        pdf_dir = self.prefix_cache_dir("pdfs")
        os.makedirs(pdf_dir)
        for pdf_file in tqdm(hrefs, desc="wgetting pdfs-files"):
            wget_file(f"{url}/{pdf_file}", pdf_dir)


if __name__ == "__main__":
    url = "https://elecciones1.registraduria.gov.co/esc_cong_2018/archivos/divulgacion/"
    WgetPdfs(url=url, cache_base=os.environ["DATA_PATH"])
