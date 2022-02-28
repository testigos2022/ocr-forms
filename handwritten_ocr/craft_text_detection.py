# import Craft class
import os
from dataclasses import dataclass, field
from typing import Union, Iterable, Iterator

from craft_text_detector import Craft
from tqdm import tqdm

# set image path and export folder directory
# image_file = "handwritten_ocr/data/esc_cong_2018_archivos_divulgacion_AGE_XXX_2_01_004_XXX_XX_XX_X_1052_F_49/esc_cong_2018_archivos_divulgacion_AGE_XXX_2_01_004_XXX_XX_XX_X_1052_F_49.pdf-0.jpg"  # can be filepath, PIL image or numpy array
from misc_utils.cached_data_specific import CachedDataclasses
from misc_utils.dataclass_utils import UNDEFINED, _UNDEFINED
from misc_utils.prefix_suffix import PrefixSuffix


@dataclass
class CroppedImage:
    image_file: PrefixSuffix
    cropped_image_file: PrefixSuffix
    box: list[list[float]]


@dataclass
class CraftCroppedImages(CachedDataclasses[CroppedImage]):
    name: Union[_UNDEFINED, str] = UNDEFINED
    image_files: Union[_UNDEFINED, Iterable[PrefixSuffix]] = UNDEFINED
    cache_base: PrefixSuffix = field(
        default_factory=lambda: PrefixSuffix("cache_root", "cropped_images")
    )

    @property
    def output_dir(self):
        return self.prefix_cache_dir("data")

    def generate_dataclasses_to_cache(self) -> Iterator[CroppedImage]:
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
            r = craft.detect_text(str(f))
            for crop_file, b in zip(r["text_crop_paths"], r["boxes"]):
                yield CroppedImage(
                    image_file=self.cache_dir.from_str_same_prefix(str(f)),
                    cropped_image_file=self.cache_dir.from_str_same_prefix(crop_file),
                    box=b.tolist(),
                )

        craft.unload_craftnet_model()
        craft.unload_refinenet_model()
