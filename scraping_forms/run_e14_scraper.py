import os
import shutil
import sys
sys.path.append("")

from scraping_forms.scrape_election_forms import E14Cong2018
from scraping_forms.nested_dropdowns import DropDownSelection


if __name__ == "__main__":
    data_path=os.environ["DATA_PATH"]


    scraper = E14Cong2018(
        base_url="https://elecciones1.registraduria.gov.co",
        url=f"https://elecciones1.registraduria.gov.co/e14_cong_2018/",
        download_path=f"{data_path}/e14_cong_2018/downloads",
        data_dir=f"{data_path}/e14_cong_2018/data",
        selections=[
            DropDownSelection("departamento", '//*[@id="select_dep"]'),
            DropDownSelection("municipio", '//*[@id="mpio"]'),
            DropDownSelection("zona", '//*[@id="zona"]'),
            DropDownSelection("puesto", '//*[@id="pto"]'),
        ],
        between_two_pdfs_wait_time=.1,
        headless=False # just for fun, to see how it is working
    )
    scraper.run()