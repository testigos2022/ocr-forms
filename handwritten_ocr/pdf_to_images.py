import os
from pathlib import Path

from pdf2image import convert_from_path
from tqdm import tqdm

if __name__ == "__main__":
    #    pip install pdf2image
    # data_path = os.environ["DATA_PATH"]
    data_path="handwritten_ocr/data"
    # pdf_file = f"{data_path}/esc_cong_2018/data/esc_cong_2018_archivos_divulgacion_AGE_XXX_2_01_004_XXX_XX_XX_X_1052_F_49.pdf"
    pdf_file = f"{data_path}/esc_cong_2018_archivos_divulgacion_AGE_XXX_2_01_004_XXX_XX_XX_X_1052_F_49.pdf"
    pages = convert_from_path(pdf_file, 200)
    output_dir = f"{data_path}/{Path(pdf_file).stem}"
    os.makedirs(output_dir, exist_ok=True)
    for k, page in tqdm(enumerate(pages)):
        page.save(f"{output_dir}/{Path(pdf_file).name}-{k}.jpg", "JPEG")
