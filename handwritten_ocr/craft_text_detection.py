# import Craft class
from craft_text_detector import Craft

# set image path and export folder directory
image = "scraping_forms/images/sample.png"  # can be filepath, PIL image or numpy array
output_dir = "outputs/"

craft = Craft(output_dir=output_dir, crop_type="poly", cuda=False)

prediction_result = craft.detect_text(image)

craft.unload_craftnet_model()
craft.unload_refinenet_model()
