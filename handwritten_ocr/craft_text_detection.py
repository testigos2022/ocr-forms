# import Craft class
from pathlib import Path

from craft_text_detector import Craft

# set image path and export folder directory
image_file = "handwritten_ocr/data/esc_cong_2018_archivos_divulgacion_AGE_XXX_2_01_004_XXX_XX_XX_X_1052_F_49/esc_cong_2018_archivos_divulgacion_AGE_XXX_2_01_004_XXX_XX_XX_X_1052_F_49.pdf-0.jpg"  # can be filepath, PIL image or numpy array
output_dir = f"handwritten_ocr/data/{Path(image_file).stem}"

craft = Craft(
    output_dir=output_dir,
    text_threshold=0.25,
    crop_type="poly",
    low_text=0.3,
    long_size=2000,
    cuda=False,
)

prediction_result = craft.detect_text(image_file)

craft.unload_craftnet_model()
craft.unload_refinenet_model()
