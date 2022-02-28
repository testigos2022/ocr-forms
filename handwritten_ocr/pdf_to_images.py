import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Union, Iterator, Iterable

from PIL.PpmImagePlugin import PpmImageFile
from misc_utils.cached_data import CachedData
from misc_utils.dataclass_utils import _UNDEFINED, UNDEFINED
from misc_utils.prefix_suffix import PrefixSuffix, BASE_PATHES
from pdf2image import convert_from_path
from tqdm import tqdm

from misc_utils.buildable import Buildable


@dataclass
class CroppedImages(CachedData, Iterable[str]):
    pdf_file: Union[_UNDEFINED, str] = UNDEFINED
    x_window_scale: int = 1
    y_window_scale: int = 3
    x_step_size_fun: Callable[[PpmImageFile], int] = field(
        default=lambda page: round(page.width - 1)
    )
    y_step_size_fun: Callable[[PpmImageFile], int] = field(
        default=lambda page: round(1.41 * page.width / 30)
    )

    @property
    def name(self):
        return Path(self.pdf_file).name

    @property
    def output_dir(self):
        return self.prefix_cache_dir("cropped_images")

    def _build_cache(self):
        pages = convert_from_path(pdf_file, 200)
        for k, page in tqdm(enumerate(pages)):
            self._process_page(k, page)

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
        page_dir = f"{self.output_dir}/{Path(pdf_file).name}-{k}"
        os.makedirs(page_dir, exist_ok=True)
        for b in tqdm(self.generate_cropboxes(page, x_step, y_step)):
            (x, y, x1, y1) = b
            cropped = page.crop(b)
            cropped.save(f"{page_dir}/cropped_{x}_{y}.jpg", "JPEG")
        page.save(f"{self.output_dir}/{Path(pdf_file).name}-{k}.jpg", "JPEG")

    def __iter__(self) -> Iterator[str]:
        for p in Path(self.output_dir).rglob("cropped*.jpg"):
            yield str(p)


@dataclass
class ImagesFromPdf(CachedData, Iterable[str]):
    pdf_file: Union[_UNDEFINED, str] = UNDEFINED

    @property
    def name(self):
        return Path(self.pdf_file).name

    @property
    def output_dir(self):
        return self.prefix_cache_dir("data")

    def _build_cache(self):
        os.makedirs(self.output_dir, exist_ok=True)

        pages = convert_from_path(pdf_file, 200)
        for k, page in tqdm(enumerate(pages)):
            page.save(f"{self.output_dir}/{Path(pdf_file).name}-{k}.jpg", "JPEG")

    def __iter__(self):
        for p in Path(self.output_dir).rglob(f"*.jpg"):
            yield str(p)


if __name__ == "__main__":
    #    pip install pdf2image
    data_path = os.environ["DATA_PATH"]
    BASE_PATHES["cache_root"] = f"{data_path}/cache"

    # pdf_file = f"{data_path}/esc_cong_2018/data/esc_cong_2018_archivos_divulgacion_AGE_XXX_2_01_004_XXX_XX_XX_X_1052_F_49.pdf"
    # pdf_file = f"{data_path}/esc_cong_2018_archivos_divulgacion_AGE_XXX_2_01_004_XXX_XX_XX_X_1052_F_49.pdf"
    pdf_file = f"{data_path}/e14_cong_2018__e14_divulgacion_01_001_001_CAM_E14_CAM_X_01_001_001_XX_01_005_X_XXX.pdf"
    CroppedImages(
        pdf_file=pdf_file,
        cache_base=PrefixSuffix("cache_root", "cropped_images"),
        x_window_scale=1,
        y_window_scale=3,
    ).build()
