# https://github.com/NielsRogge/Transformers-Tutorials/blob/master/TrOCR/Evaluating_TrOCR_base_handwritten_on_the_IAM_test_set.ipynb
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Union, Optional

import numpy as np
import torch
from PIL import Image
from beartype import beartype
from numpy.typing import NDArray
from tqdm import tqdm
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from data_io.readwrite_files import read_jsonl
from handwritten_ocr.craft_text_detection import CraftCroppedImages, CroppedImage
from handwritten_ocr.pdf_to_images import ImagesFromPdf
from misc_utils.buildable import Buildable
from misc_utils.cached_data_specific import CachedDataclasses
from misc_utils.dataclass_utils import (
    _UNDEFINED,
    UNDEFINED,
    decode_dataclass,
)
from misc_utils.prefix_suffix import BASE_PATHES, PrefixSuffix
from misc_utils.processing_utils import iterable_to_batches


@dataclass
class EmbeddedImage(CroppedImage):
    bucket_file: PrefixSuffix
    bucket_index: int
    _array: Optional[NDArray] = field(init=True, default=None, repr=False)

    @property
    def array(self) -> NDArray:
        if self._array is None:
            self._array = np.load(f"{self.bucket_file}")[self.bucket_index]
        return self._array

    @beartype
    def set_array(self, array: NDArray):
        self._array = array


@dataclass
class OCRInferencer(Buildable):
    model_name: str = "microsoft/trocr-base-handwritten"

    def _build_self(self) -> Any:
        self.processor = TrOCRProcessor.from_pretrained(self.model_name)
        self.model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
        self.model.eval()

    def ocr_file(self, file: str) -> str:
        # https://huggingface.co/docs/transformers/v4.15.0/en/model_doc/trocr
        pixel_values = self._pixel_values_from_file(file)
        generated_ids = self.model.generate(pixel_values)
        generated_text = self.processor.batch_decode(
            generated_ids, skip_special_tokens=True
        )[0]
        return generated_text

    def _pixel_values_from_file(self, file):
        image = Image.open(file).convert("RGB")
        pixel_values = self.processor(image, return_tensors="pt").pixel_values
        return pixel_values

    @beartype
    def embedd_image(self, image_file: str) -> torch.Tensor:
        with torch.no_grad():
            pixel_values = self._pixel_values_from_file(image_file)
            encoder_output = self.model.encoder(pixel_values)
            embedding = encoder_output.pooler_output.squeeze()
        return embedding


@dataclass
class EmbeddedData(CachedDataclasses[EmbeddedImage]):
    name: Union[_UNDEFINED, str] = UNDEFINED
    images: Union[_UNDEFINED, CraftCroppedImages] = UNDEFINED
    inferencer: Union[_UNDEFINED, OCRInferencer] = UNDEFINED
    bucket_size: int = 100

    cache_base: PrefixSuffix = field(
        default_factory=lambda: PrefixSuffix("cache_root", "embeddings")
    )

    @property
    def data_folder(self):
        return self.prefix_cache_dir("data")

    def generate_dataclasses_to_cache(self) -> Iterator[EmbeddedImage]:
        os.makedirs(self.data_folder, exist_ok=True)
        yield from self._dump_batches()

    def _dump_batches(self):
        g = (
            (
                im,
                self.inferencer.embedd_image(str(im.cropped_image_file))
                .detach()
                .numpy(),
            )
            for im in tqdm(self.images, desc="embedding images")
        )

        for k, bucket in enumerate(iterable_to_batches(g, batch_size=self.bucket_size)):
            bucket: list[tuple[CroppedImage, NDArray]]
            concat_array = np.concatenate([a for i, a in bucket])
            bucket_file_name = f"bucket-{k}.npy"
            bucket_file = f"{self.data_folder}/{bucket_file_name}"
            np.save(bucket_file, concat_array)
            yield from [
                EmbeddedImage(
                    image_file=i.image_file,
                    cropped_image_file=i.cropped_image_file,
                    box=i.box,
                    bucket_file=self.cache_dir.from_str_same_prefix(bucket_file),
                    bucket_index=bidx,
                )
                for bidx, (i, a) in enumerate(bucket)
            ]

    def __iter__(self) -> Iterator[EmbeddedImage]:
        g: Iterable[EmbeddedImage] = (
            decode_dataclass(d) for d in read_jsonl(self.jsonl_file)
        )
        bucketfile2datum = {d.bucket_file: d for d in g}
        for p in Path(self.data_folder).glob("*.npy"):
            batch_array = np.load(str(p))
            for k, a in enumerate(batch_array):
                datum: EmbeddedImage = bucketfile2datum[p.name]
                assert k == datum.bucket_index
                datum.set_array(a)
                yield datum


if __name__ == "__main__":
    data_path = os.environ["DATA_PATH"]
    BASE_PATHES["data_path"] = f"{data_path}"
    BASE_PATHES["cache_root"] = f"{data_path}/cache"
    # # file = f"{data_path}/esc_cong_2018/jpegs/esc_cong_2018_archivos_divulgacion_AGE_XXX_2_01_004_XXX_XX_XX_X_1052_F_49.pdf-0.jpg"
    # file = "handwritten_ocr/images/single_line_right.png"
    # # file="handwritten_ocr/images/none_none_5.jpg"
    # model = OCRInferencer(model_name="microsoft/trocr-large-handwritten").build()
    # # print(model.ocr_file(file))
    # print(f"{model.embedd_file(file).shape=}")

    EmbeddedData(
        name="debug",
        inferencer=OCRInferencer(model_name="microsoft/trocr-base-handwritten"),
        images=CraftCroppedImages(
            name="debug",
            image_files=ImagesFromPdf(
                pdf_file=PrefixSuffix(
                    "data_path",
                    "handwritten_ocr/data/e14_cong_2018__e14_divulgacion_01_001_001_CAM_E14_CAM_X_01_001_001_XX_01_005_X_XXX.pdf",
                )
            ),
        ),
    ).build()

"""
microsoft/trocr-large-printed on single_line_right.png
NO.98499041, JUEZ, EL(IA) DOCTOR(A

TODO: microsoft/trocr-base-handwritten -> not really working!
"""
