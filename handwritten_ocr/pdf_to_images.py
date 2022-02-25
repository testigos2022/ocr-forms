import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from PIL.PpmImagePlugin import PpmImageFile
from pdf2image import convert_from_path
from tqdm import tqdm

from misc_utils.buildable import Buildable


@dataclass
class CroppedImages(Buildable):
    pdf_file: str
    output_dir: str
    x_window_scale: int = 1
    y_window_scale: int = 3
    x_step_size_fun: Callable[[PpmImageFile], int] = field(
        default=lambda page: round(page.width - 1)
    )
    y_step_size_fun: Callable[[PpmImageFile], int] = field(
        default=lambda page: round(1.41 * page.width / 30)
    )

    def _build_self(self) -> Any:
        pages = convert_from_path(pdf_file, 200)
        for k, page in tqdm(enumerate(pages)):
            self._process_page(k, page)
            break

    def generate_cropboxes(self, page, x_step, y_step):
        for x in range(0, page.width - x_step, x_step):
            for y in range(0, page.height - y_step, y_step):
                x1, y1 = (
                    x + x_step * self.x_window_scale,
                    y + y_step * self.y_window_scale,
                )
                yield x, y, x1, y1

    def _process_page(self, k, page: PpmImageFile):
        x_step = self.x_step_size_fun(page)
        y_step = self.y_step_size_fun(page)
        print(f"{type(page)}")
        print(f"{page.width=},{page.height=}")
        page_dir = f"{output_dir}/{Path(pdf_file).name}-{k}"
        os.makedirs(page_dir, exist_ok=True)
        for b in tqdm(self.generate_cropboxes(page, x_step, y_step)):
            (x, y, x1, y1) = b
            cropped = page.crop(b)
            cropped.save(f"{page_dir}/cropped_{x}_{y}.jpg", "JPEG")
        page.save(f"{output_dir}/{Path(pdf_file).name}-{k}.jpg", "JPEG")


if __name__ == "__main__":
    #    pip install pdf2image
    data_path = os.environ["DATA_PATH"]
    # pdf_file = f"{data_path}/esc_cong_2018/data/esc_cong_2018_archivos_divulgacion_AGE_XXX_2_01_004_XXX_XX_XX_X_1052_F_49.pdf"
    # pdf_file = f"{data_path}/esc_cong_2018_archivos_divulgacion_AGE_XXX_2_01_004_XXX_XX_XX_X_1052_F_49.pdf"
    pdf_file = f"{data_path}/e14_cong_2018__e14_divulgacion_01_001_001_CAM_E14_CAM_X_01_001_001_XX_01_005_X_XXX.pdf"
    output_dir = f"{data_path}/{Path(pdf_file).stem}"
    os.makedirs(output_dir, exist_ok=True)
    CroppedImages(
        pdf_file=pdf_file, output_dir=output_dir, x_window_scale=1, y_window_scale=3
    ).build()
