# pylint: skip-file
import gzip
import itertools
import json
import locale
import os
import re
import tarfile
from typing import Dict, Iterator, Callable, Optional, Tuple, TypeVar, Any
from typing import Iterable

from beartype import beartype

assert locale.getpreferredencoding(False) == "UTF-8"


def write_jsonl(file: str, data: Iterable[Dict], mode="wb"):
    def process_line(d: Dict):
        line = json.dumps(d, skipkeys=True, ensure_ascii=False)
        line = line + "\n"
        if "b" in mode:
            line = line.encode("utf-8")
        return line

    with gzip.open(file, mode=mode) if file.endswith("gz") else open(
        file, mode=mode
    ) as f:
        f.writelines(process_line(d) for d in data)


def write_json(file: str, datum: Dict, mode="wb"):
    with gzip.open(file, mode=mode) if file.endswith("gz") else open(
        file, mode=mode
    ) as f:
        line = json.dumps(datum, skipkeys=True, ensure_ascii=False)
        if "b" in mode:
            line = line.encode("utf-8")
        f.write(line)


def write_file(file, s: str, mode="wb"):
    with gzip.open(file, mode=mode) if file.endswith(".gz") else open(
        file, mode=mode
    ) as f:
        f.write(s.encode("utf-8"))


def read_file(file, encoding="utf-8"):
    file_io = (
        gzip.open(file, mode="r", encoding=encoding)
        if file.endswith(".gz")
        else open(file, mode="r", encoding=encoding)
    )
    with file_io as f:
        return f.read()


def write_lines(file, lines: Iterable[str], mode="wb"):
    def process_line(line):
        line = line + "\n"
        if "b" in mode:  # useful for "text"-mode "t" which uses line-wise buffering
            line = line.encode("utf-8")
        return line

    with gzip.open(file, mode=mode) if file.endswith(".gz") else open(
        file, mode=mode
    ) as f:
        f.writelines(process_line(l) for l in lines)


@beartype
def write_csv(
    file: str, data: Iterable[tuple[str]], header: list[str], delimiter: str = "\t"
):
    write_lines(
        file, (delimiter.join(row) for row in itertools.chain([tuple(header)], data))
    )


@beartype
def write_dicts_to_csv(
    file: str,
    data: Iterable[dict[str, Any]],
    header: Optional[list[str]] = None,
    delimiter: str = "\t",
):
    def gen_rows(header: Optional[list[str]]):
        if header is not None:
            yield header
        for datum in data:
            if header is None:
                header = list(datum.keys())
                yield delimiter.join(header)
            yield delimiter.join([datum.get(k, None) for k in header])

    write_lines(file, gen_rows(header))


def read_lines_from_files(path: str, mode="b", encoding="utf-8", limit=None):
    g = (
        line
        for file in os.listdir(path)
        for line in read_lines(os.path.join(path, file), mode, encoding)
    )
    for c, line in enumerate(g):
        if limit and (c >= limit):
            break
        yield line


def read_lines(file, encoding="utf-8", limit=None, num_to_skip=0) -> Iterator[str]:
    mode = "rb"
    file_io = (
        gzip.open(file, mode=mode)
        if file.endswith(".gz")
        else open(file, mode=mode)  # pylint: disable=consider-using-with
    )
    with file_io as f:
        _ = [next(f) for _ in range(num_to_skip)]
        for counter, line in enumerate(f):
            if limit is not None and (counter >= limit):
                break
            if "b" in mode:
                line = line.decode(encoding)
            yield line.replace("\n", "")


def read_jsonl(
    file, encoding="utf-8", limit=None, num_to_skip=0
) -> Iterator[dict[str, Any]]:
    for l in read_lines(file, encoding, limit, num_to_skip):
        yield json.loads(l)


def read_json(file: str, mode="b"):
    with gzip.open(file, mode="r" + mode) if file.endswith("gz") else open(
        file, mode="r" + mode
    ) as f:
        s = f.read()
        s = s.decode("utf-8") if mode == "b" else s  # type: ignore
        return json.loads(s)


# @beartype
def filter_gen_targz_members(
    targz_file: str,
    is_of_interest_fun: Callable[[tarfile.TarInfo], bool],
    start: Optional[int] = None,
    stop: Optional[int] = None,
    verbose=False,
) -> Iterator[
    Tuple[tarfile.TarInfo, tarfile.ExFileObject]
]:  # TODO(tilo): am I sure about IO as type?
    with tarfile.open(targz_file, "r:gz") as tar:
        for k, member in enumerate(itertools.islice(tar, start, stop)):
            if verbose and k % 10_000 == 0:
                print(f"at position {k} in {targz_file}")
            member: tarfile.TarInfo
            if is_of_interest_fun(member):
                f: tarfile.ExFileObject = tar.extractfile(member)  # type: ignore
                # https://stackoverflow.com/questions/37474767/read-tar-gz-file-in-python
                # tarfile.extractfile() can return None if the member is neither a file nor a link.
                neither_file_nor_link = f is None
                if not neither_file_nor_link:
                    yield (member, f)
