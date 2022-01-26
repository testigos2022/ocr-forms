# ocr colombian elections form
### 1.getting (scraping) data
#### esc_cong_2018
```shell
ls WgetPdfs-esc_cong_2018-64ef3d6edcc9a7961dab1c80f2d9e07569e82362/pdfs/ |  rg -o  "^.{7}" | uniq -c | sort -r | less
   2356 E26_SEN
   2341 E26_CAM
   2340 E24_SEN
   2326 E24_CAM
   2240 AGE_XXX
     13 AUD_XXX
```
#### e14_cong_2018
* ![see](scraping_forms)

### 2. processing pdfs (OCR)
1. simple: ocrmypdf + pdfminer -> convert pdf to html
   * ![pdf to html example](handwritten_ocr/resources/E24_CAM_2_50_050_XXX_XX_XX_M_9375_F_49.html) 
2. some deep learning: [CRAFT](https://github.com/clovaai/CRAFT-pytorch) + [clovaai-text-recognition](https://github.com/clovaai/deep-text-recognition-benchmark)
3. proper ["layout/form-understanding"](https://github.com/NielsRogge/Transformers-Tutorials/tree/master/LayoutLMv2) and [advanced OCR](https://huggingface.co/docs/transformers/model_doc/trocr)
