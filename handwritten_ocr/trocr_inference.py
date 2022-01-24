# https://github.com/NielsRogge/Transformers-Tutorials/blob/master/TrOCR/Evaluating_TrOCR_base_handwritten_on_the_IAM_test_set.ipynb
import os
from dataclasses import dataclass
from typing import Any

from transformers import TrOCRProcessor, VisionEncoderDecoderModel

import requests

from PIL import Image

from misc_utils.buildable import Buildable


@dataclass
class OCRInferencer(Buildable):
    model_name: str = "microsoft/trocr-base-handwritten"

    def _build_self(self) -> Any:
        self.processor = TrOCRProcessor.from_pretrained(self.model_name)
        self.model = VisionEncoderDecoderModel.from_pretrained(self.model_name)

    def ocr_file(self, file: str) -> str:
        # https://huggingface.co/docs/transformers/v4.15.0/en/model_doc/trocr
        image = Image.open(file).convert("RGB")
        pixel_values = self.processor(image, return_tensors="pt").pixel_values
        print(f"{pixel_values.shape=}")
        generated_ids = self.model.generate(pixel_values)
        generated_text = self.processor.batch_decode(
            generated_ids, skip_special_tokens=True
        )[0]
        return generated_text


if __name__ == "__main__":
    # data_path = os.environ["DATA_PATH"]
    # file = f"{data_path}/esc_cong_2018/jpegs/esc_cong_2018_archivos_divulgacion_AGE_XXX_2_01_004_XXX_XX_XX_X_1052_F_49.pdf-0.jpg"
    file="handwritten_ocr/images/single_line_right.png"
    model = OCRInferencer(model_name='microsoft/trocr-base-printed').build()
    print(model.ocr_file(file))

"""
PATINO identificadolaj con C.C. No.98499041,
TODO: microsoft/trocr-base-handwritten -> not really working!
"""