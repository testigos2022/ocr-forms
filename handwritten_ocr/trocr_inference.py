# https://github.com/NielsRogge/Transformers-Tutorials/blob/master/TrOCR/Evaluating_TrOCR_base_handwritten_on_the_IAM_test_set.ipynb
import os
from abc import abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Union

import numpy as np
from misc_utils.prefix_suffix import BASE_PATHES, PrefixSuffix
from numpy.typing import NDArray
from tqdm import tqdm
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

import requests

from PIL import Image

from data_io.readwrite_files import write_jsonl, read_jsonl
from misc_utils.buildable import Buildable
from misc_utils.cached_data import CachedData
from misc_utils.dataclass_utils import (
    _UNDEFINED,
    UNDEFINED,
    to_dict,
    decode_dataclass,
    encode_dataclass,
)
from misc_utils.processing_utils import iterable_to_batches

from handwritten_ocr.craft_text_detection import CraftCroppedImages
from handwritten_ocr.pdf_to_images import CroppedImages, ImagesFromPdf


@dataclass
class EmbeddedFile:
    file: PrefixSuffix
    array: NDArray


@dataclass
class OCRInferencer(Buildable):
    model_name: str = "microsoft/trocr-base-handwritten"

    def _build_self(self) -> Any:
        self.processor = TrOCRProcessor.from_pretrained(self.model_name)
        self.model = VisionEncoderDecoderModel.from_pretrained(self.model_name)

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
        # print(f"{pixel_values.shape=}")
        return pixel_values

    def embedd_file(self, file: PrefixSuffix):
        pixel_values = self._pixel_values_from_file(str(file))
        encoder_output = self.model.encoder(pixel_values)
        embedding = encoder_output.pooler_output.squeeze()
        return EmbeddedFile(file=file, array=embedding.detach().numpy())


@dataclass
class EmbeddingsIter(Buildable, Iterable[EmbeddedFile]):
    @abstractmethod
    def __iter__(self) -> Iterator[EmbeddedFile]:
        raise NotImplementedError


@dataclass
class TrOCREmbeddings(EmbeddingsIter):
    inferencer: OCRInferencer
    files: Iterable[PrefixSuffix]

    def __iter__(self) -> Iterator[EmbeddedFile]:
        for f in self.files:
            yield self.inferencer.embedd_file(f)


@dataclass
class ManifestDatum:
    file: PrefixSuffix
    bucket_file_name: str
    bucket_index: int


@dataclass
class EmbeddedData(CachedData):
    name: Union[_UNDEFINED, str] = UNDEFINED
    embeddings: Union[_UNDEFINED, EmbeddingsIter] = UNDEFINED
    bucket_size: int = 100

    cache_base: PrefixSuffix = field(
        default_factory=lambda: PrefixSuffix("cache_root", "embeddings")
    )

    @property
    def data_folder(self):
        return self.prefix_cache_dir("data")

    def _build_cache(self):
        os.makedirs(self.data_folder, exist_ok=True)
        write_jsonl(
            self.manifest_file,
            (
                encode_dataclass(o)
                for o in tqdm(
                    self._dump_batches(), desc=f"writing manifest, dumping embeddings"
                )
            ),
        )

    @property
    def manifest_file(self):
        return self.prefix_cache_dir("manifest.jsonl.gz")

    def _dump_batches(self):
        for k, bucket in enumerate(
            iterable_to_batches(self.embeddings, batch_size=self.bucket_size)
        ):
            bucket: list[EmbeddedFile]
            concat_array = np.concatenate([b.array for b in bucket])
            bucket_file_name = f"bucket-{k}.npy"
            bucket_file = f"{self.data_folder}/{bucket_file_name}"
            np.save(bucket_file, concat_array)
            yield from [
                ManifestDatum(
                    file=b.file, bucket_file_name=bucket_file_name, bucket_index=bidx
                )
                for bidx, b in enumerate(bucket)
            ]

    def __iter__(self) -> Iterator[EmbeddedFile]:
        g = (decode_dataclass(d) for d in read_jsonl(self.manifest_file))
        bucketfile2datum = {d.bucket_file_name: d for d in g}
        for p in Path(self.data_folder).glob("*.npy"):
            batch_array = np.load(str(p))
            for k, a in enumerate(batch_array):
                datum: ManifestDatum = bucketfile2datum[p.name]
                yield EmbeddedFile(file=datum.file, array=a)


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
        embeddings=TrOCREmbeddings(
            inferencer=OCRInferencer(model_name="microsoft/trocr-base-handwritten"),
            files=CraftCroppedImages(
                name="debug",
                image_files=ImagesFromPdf(
                    pdf_file=PrefixSuffix(
                        "data_path",
                        "handwritten_ocr/data/e14_cong_2018__e14_divulgacion_01_001_001_CAM_E14_CAM_X_01_001_001_XX_01_005_X_XXX.pdf",
                    )
                ),
            ),
        ),
    ).build()

"""
microsoft/trocr-large-printed on single_line_right.png
NO.98499041, JUEZ, EL(IA) DOCTOR(A

TODO: microsoft/trocr-base-handwritten -> not really working!
"""
