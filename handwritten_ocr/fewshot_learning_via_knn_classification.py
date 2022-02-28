import itertools
import os
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

from data_io.readwrite_files import read_lines, write_file
from handwritten_ocr.craft_text_detection import CraftCroppedImages
from handwritten_ocr.pdf_to_images import ImagesFromPdf
from handwritten_ocr.trocr_inference import OCRInferencer, EmbeddedData
from misc_utils.prefix_suffix import PrefixSuffix
from misc_utils.utils import build_markdown_table_from_dicts


def image_in_markdown(f):
    return f"![]({f})"


def parse_table_row_line(l):
    def strip_away(x):
        x = x.strip(" ![]()")
        return x

    idx, label, file = [strip_away(s) for s in l.split("|")]
    return int(idx), int(label), file


if __name__ == "__main__":
    #
    # annotated_data=[
    #     {"idx": 0, "label": 1, "image": image_in_markdown(
    #         "data/e14_cong_2018__e14_divulgacion_01_001_001_CAM_E14_CAM_X_01_001_001_XX_01_005_X_XXX/e14_cong_2018__e14_divulgacion_01_001_001_CAM_E14_CAM_X_01_001_001_XX_01_005_X_XXX.pdf-2/cropped_0_3680.jpg")},
    #     {"idx": 1, "label": 0, "image": image_in_markdown(
    #         "data/e14_cong_2018__e14_divulgacion_01_001_001_CAM_E14_CAM_X_01_001_001_XX_01_005_X_XXX/e14_cong_2018__e14_divulgacion_01_001_001_CAM_E14_CAM_X_01_001_001_XX_01_005_X_XXX.pdf-0/cropped_0_0.jpg")}
    # ]

    data_path = os.environ["DATA_PATH"]

    embedded_data = EmbeddedData(
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

    # write_file("annotations.md",build_markdown_table_from_dicts(annotated_data))
    train_data = [
        parse_table_row_line(l)
        for l in read_lines("annotations.md")
        if not any([l.startswith(s) for s in ["---", "idx"]])
    ]
    print(train_data)

    file_embeddings = [
        (f, embedder.embedd_image(f"{data_path}/{f}").detach().numpy())
        for _, _, f in train_data
    ]
    X = np.concatenate([[x] for _, x in file_embeddings])
    print(f"{X.shape=}")
    # y = np.array([y for _, y, _ in examples])
    # n_neighbors = 1
    # weights = "distance"
    # clf = neighbors.KNeighborsClassifier(n_neighbors, weights=weights)
    # clf.fit(X, y)

    path = f"{data_path}/e14_cong_2018__e14_divulgacion_01_001_001_CAM_E14_CAM_X_01_001_001_XX_01_005_X_XXX.pdf-0/e14_cong_2018__e14_divulgacion_01_001_001_CAM_E14_CAM_X_01_001_001_XX_01_005_X_XXX.pdf-0_crops"
    files = Path(path).rglob("crop_*.png")

    def get_predictions(p):
        x = embedder.embedd_image(str(p))
        x = x.detach().numpy()
        # x = np.expand_dims(x, 0)
        # o = clf.predict_proba(x).squeeze()
        # o=cosine_similarity(x,np.expand_dims(X[0],0))
        return x

    files = list(itertools.islice(files, 0, 100))
    file_embeddings_unlabeled = (
        (
            str(p).replace(f"{base_path}/", ""),
            get_predictions(p),
        )
        for p in files
    )
    unlabeled = np.array(
        [x for _, x in tqdm(file_embeddings_unlabeled, desc="calc embeddings")]
    )
    print(f"{unlabeled.shape=}")

    pipeline = Pipeline(
        [("scaling", StandardScaler()), ("pca", PCA(random_state=42, n_components=20))]
    )
    # print(f"{std_scaler.mean_=},{std_scaler.scale_=}")
    unlabeld_svd = pipeline.fit_transform(unlabeled)
    labeled_svd = pipeline.transform(X)
    print(f"{unlabeld_svd.shape=},{labeled_svd.shape=}")
    print(f"{unlabeld_svd=},{labeled_svd=}")
    sims = cosine_similarity(labeled_svd, unlabeld_svd).squeeze()
    print(f"{sims.shape=}")
    g = (
        {
            "idx": k,
            "cosine_similarity": sim,
            "image": image_in_markdown(file),
        }
        for k, (sim, file) in enumerate(zip(sims, files))
    )
    write_file(
        f"predictions.md",
        build_markdown_table_from_dicts(
            sorted(g, key=lambda d: d["cosine_similarity"], reverse=True)
        ),
    )
