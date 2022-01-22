import sys

sys.path.append(".")

import os

from scraping_forms.nested_dropdowns import DropDownSelection
from scraping_forms.scrape_election_forms import ESCCong

if __name__ == "__main__":
    data_path = os.environ["DATA_PATH"]

    scraper = ESCCong(
        data_dir=f"{data_path}/esc_cong_2018/data",
        base_url="https://elecciones1.registraduria.gov.co",
        url=f"https://elecciones1.registraduria.gov.co/esc_cong_2018/",
        download_path=f"{data_path}/esc_cong_2018/downloads",
        selections=[
            DropDownSelection(
                "corporacion",
                "/html/body/div/div[2]/div[3]/div/div[1]/div/form/div[1]/select",
            ),
            DropDownSelection(
                "departamento",
                "/html/body/div/div[2]/div[3]/div/div[1]/div/form/div[2]/select",
            ),
            DropDownSelection(
                "municipio",
                "/html/body/div/div[2]/div[3]/div/div[1]/div/form/div[3]/div/select",
            ),
            DropDownSelection(
                "zona",
                "/html/body/div/div[2]/div[3]/div/div[1]/div/form/div[4]/div/select",
            ),
        ],
        option_blacklist=["Corporación", "Departamento", "Municipio"],
        headless=False,
    )
    scraper.run()
