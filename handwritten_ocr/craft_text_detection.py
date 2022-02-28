# import Craft class
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union, Iterable, Iterator

from craft_text_detector import Craft

# set image path and export folder directory
# image_file = "handwritten_ocr/data/esc_cong_2018_archivos_divulgacion_AGE_XXX_2_01_004_XXX_XX_XX_X_1052_F_49/esc_cong_2018_archivos_divulgacion_AGE_XXX_2_01_004_XXX_XX_XX_X_1052_F_49.pdf-0.jpg"  # can be filepath, PIL image or numpy array
from misc_utils.cached_data import CachedData
from misc_utils.dataclass_utils import UNDEFINED, _UNDEFINED
from misc_utils.prefix_suffix import PrefixSuffix
from tqdm import tqdm


@dataclass
class CraftCroppedImages(CachedData, Iterable[str]):
    name: Union[_UNDEFINED, str] = UNDEFINED
    image_files: Union[_UNDEFINED, Iterable[str]] = UNDEFINED
    cache_base: PrefixSuffix = field(
        default_factory=lambda: PrefixSuffix("cache_root", "cropped_images")
    )

    @property
    def output_dir(self):
        return self.prefix_cache_dir("data")

    def _build_cache(self):
        os.makedirs(self.output_dir, exist_ok=True)

        craft = Craft(
            output_dir=self.output_dir,
            text_threshold=0.25,
            crop_type="poly",
            low_text=0.3,
            long_size=2000,
            cuda=False,
        )
        for f in tqdm(self.image_files, desc="craft-detecting"):
            prediction_result = craft.detect_text(f)

        craft.unload_craftnet_model()
        craft.unload_refinenet_model()

    def __iter__(self) -> Iterator[str]:
        for p in Path(self.output_dir).rglob("crop*.png"):
            yield str(p)
