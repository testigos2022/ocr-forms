import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import itertools
from tqdm import tqdm

from scraping_forms.processing_utils import exec_command
from scraping_forms.readwrite_files import read_file
from scraping_forms.utils import just_try

TOKEN = os.environ["TOKEN"]


def upload_file(collection_uuid: str, file: str):
    cmd = f'curl -q -X POST https://shuttle-4.estuary.tech/content/add?collection={collection_uuid} -H "Authorization: Bearer {TOKEN}" -H "Accept: application/json" -H "Content-Type: multipart/form-data" -F "data=@{file}"'
    s = subprocess.check_output(cmd, shell=True)
    cid = json.loads(s.decode("utf8"))["cid"]
    return True


@dataclass
class Uploader:
    collection_uuid: str
    base_path: str

    def run(self):
        pdf_dir = f"{self.base_path}/data"
        already_uploaded_content = f"{self.base_path}/already_uploaded_content.txt"
        cmd = f'curl -X GET -H "Authorization: Bearer {TOKEN}" https://api.estuary.tech/collections/content/{self.collection_uuid} > {already_uploaded_content}'
        print(f"{cmd=}")
        exec_command(cmd)
        already_uploaded = list(
            set([d["name"] for d in json.loads(read_file(already_uploaded_content))])
        )
        print(f"{len(already_uploaded)=}")

        todo_files = [
            str(p)
            for p in tqdm(Path(pdf_dir).glob(f"*.pdf"), desc="finding todo_files")
            if p.name not in already_uploaded
        ]

        for f in tqdm(todo_files):
            is_good = just_try(lambda: upload_file(self.collection_uuid, f))
            if not is_good:
                print(f"{f} failed!")


if __name__ == "__main__":
    # e14_cong_2018_uuid = "99916907-50fc-465e-9004-7fcfa3ec1d1c"
    Uploader(
        collection_uuid="7d8c898f-c014-4795-bc10-f5fe8c2d6b6a",
        base_path=os.environ["DATA_PATH"],
    ).run()
