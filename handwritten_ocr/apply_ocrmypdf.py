import os
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ocrmypdf

from misc_utils.cached_data import CachedData
from misc_utils.dataclass_utils import UNDEFINED, _UNDEFINED
from misc_utils.processing_utils import exec_command


@dataclass
class OCRMyPDFsFolder(CachedData):
    folder: Union[_UNDEFINED, str] = UNDEFINED
    lang: Union[_UNDEFINED, str] = UNDEFINED
    name: Union[_UNDEFINED, str] = UNDEFINED

    def _build_cache(self):
        for pdf_file in Path(self.folder).rglob("*.*"):
            print(f"{pdf_file}")
            ouput_dir = self.prefix_cache_dir("ocred_pdfs")
            os.makedirs(ouput_dir)
            ocrmypdf.ocr(
                input_file=pdf_file,
                output_file=f"{ouput_dir}/{pdf_file.stem}_ocr.pdf",
                language="spa",
            )
            # _,e=exec_command(f"ocrmypdf -l {self.lang} -r {pdf_file} {ouput_dir}/{pdf_file.stem}_ocr.pdf")
            # if len(e)>0:
            #     print(f"failed with: {e}")
            break


if __name__ == "__main__":
    # https://ocrmypdf.readthedocs.io/en/latest/batch.html -> TODO!
    cache_base = os.environ['DATA_PATH']
    OCRMyPDFsFolder(
        name="esc_cong_2018",
        lang="spa",
        folder=f"{cache_base}/WgetPdfs-esc_cong_2018-64ef3d6edcc9a7961dab1c80f2d9e07569e82362/pdfs",
        cache_base=cache_base,
    ).build()
