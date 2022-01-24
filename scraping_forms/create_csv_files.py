import json
from pathlib import Path

import itertools
from pprint import pprint

from beartype import beartype
from tqdm import tqdm

from data_io.readwrite_files import (
    write_lines,
    read_jsonl,
    read_file,
    write_jsonl,
    write_dicts_to_csv,
)


@beartype
def recover_url(file_name: str, base_url: str) -> str:
    for s in ["E14_SEN", "FRT_SEN", "E14_CAM", "FRT_CAM"]:
        if s in file_name:
            splitter = s
            break
    else:
        raise AssertionError(f"unknown url type: {file_name}")
    prefix, suffix = file_name.split(splitter)
    url = (
        base_url
        + "e14_cong_2018//e14_divulgacion"
        + prefix.replace("e14_cong_2018__e14_divulgacion", "").replace("_", "/")
        + splitter
        + suffix
    )
    return url


def write_e14_csv_file():
    folder = f"/home/tilo/data/colombia_election_forms/e14_cong_2018"
    base_url = f"https://elecciones1.registraduria.gov.co/"
    file_url = list(
        (p.name, recover_url(p.name, base_url))
        for p in Path(f"{folder}/data").glob(f"*.pdf")
    )

    def get_fix_selection_path(s_path: list):
        selections = ["corporacion", "departamento", "municipio", "zona", "puesto"]
        if len(s_path) < 5:
            s_path = ["Senado"] + s_path

        return {n: v for n, v in zip(selections, s_path)}

    pdf2selection = {
        d["pdf_file_full"]: get_fix_selection_path(d["selection_path"])
        for d in tqdm(
            read_jsonl(f"{folder}/downloads/selection_states.jsonl"),
            desc=f"pdf2selection",
        )
        if "pdf_file_full" in d
    }
    print(f"{len(pdf2selection.keys())=}")
    for f, u in file_url:
        if f not in pdf2selection.keys():
            print(f"{f} not in selection_path")
    data_g = (
        {"file_name": f, "url": u} | pdf2selection.get(f, {}) for f, u in file_url
    )
    # header = ["file_name", "url"]+["corporacion" "departamento", "municipio", "zona", "puesto"]
    write_dicts_to_csv(
        f"{folder}/file_name_url_selection_path.csv.gz",
        data_g,
    )


def write_e24_csv_file():
    folder = f"/home/tilo/data/colombia_election_forms/esc_cong_2018"
    file_url = [
        (d["pdf_file_full"], d["pdf_url"])
        for d in read_jsonl(f"{folder}/downloads/selection_states.jsonl")
        if "pdf_file_full" in d
    ]

    def list_to_dict(s_path: list):
        selections = ["original_filename","corporacion", "departamento", "municipio", "zona"]
        assert len(s_path) == 5, f"{s_path=}"

        return {n: v for n, v in zip(selections, s_path)}

    broken_selection_pathes = {
        d["pdf_file_full"]: d["selection_path"]
        for d in tqdm(
            read_jsonl(f"{folder}/downloads/selection_states.jsonl"),
            desc=f"pdf2selection",
        )
        if "pdf_file_full" in d and len(d["selection_path"]) != 4
    }
    # pprint(broken_selection_pathes)
    print(f"got {len(broken_selection_pathes)} broken ones")
    pdf2selection = {
        d["pdf_file_full"]: list_to_dict([d["pdf_file"]]+d["selection_path"])
        for d in tqdm(
            read_jsonl(f"{folder}/downloads/selection_states.jsonl"),
            desc=f"pdf2selection",
        )
        if "pdf_file_full" in d and len(d["selection_path"]) == 4
    }
    print(f"{len(pdf2selection.keys())=}")
    for f, u in file_url:
        if f not in pdf2selection.keys():
            print(f"{f} not in selection_path")
    data_g = (
        {"file_name": f, "url": u} | pdf2selection.get(f, {}) for f, u in file_url
    )
    # header = ["file_name", "url"]+["corporacion" "departamento", "municipio", "zona", "puesto"]
    write_dicts_to_csv(
        f"{folder}/esc_cong_2018_file_name_url_selection_path.csv.gz",
        data_g,
    )


if __name__ == "__main__":
    write_e24_csv_file()
    # write_e14_csv_file()
    # write_jsonl(f"content.jsonl", (d for d in json.loads(read_file("content.txt"))))
"""
len(pdf2selection.keys())=10153
esc_cong_2018_archivos_divulgacion_E26_CAM_2_72_008_XXX_XX_XX_X_9521_F_49.pdf not in selection_path
esc_cong_2018_archivos_divulgacion_AGE_XXX_2_72_008_XXX_XX_XX_X_9521_F_49.pdf not in selection_path

len(pdf2selection.keys())=208103
e14_cong_2018__e14_divulgacion_29_001_009_SEN_E14_SEN_X_29_001_009_XX_02_008_X_XXX.pdf not in selection_path
"""
