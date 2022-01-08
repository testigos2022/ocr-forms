import random
import sys
import traceback
from dataclasses import dataclass, field
from time import time
from typing import Iterable, Callable, TypeVar, Optional, Union, Iterator, Any, Generic

from beartype import beartype

T = TypeVar("T")
T_default = TypeVar("T_default")


@beartype  # bear makes actually not sense here!?
def just_try(
    supplier: Callable[[], T],
    default: T_default = None,
    reraise: bool = False,
    verbose: bool = False,
    fail_message_builder: Optional[Callable[..., Any]] = None,
) -> Union[T, T_default]:
    try:
        return supplier()
    except Exception as e:
        if verbose:
            print(f"\ntried and failed with: {e}\n")
            traceback.print_exc(file=sys.stderr)
        if reraise:
            raise e
        if fail_message_builder is not None:
            return fail_message_builder(error=e, sys_stderr=sys.stderr)
        else:
            return default


def just_try_for_each(
    input_it: Iterable[T],
    default: T_default = None,
    break_on_failure: bool = False,
    # reraise:bool=False,
    verbose: bool = False,
) -> Iterator[Union[T, T_default]]:
    it = iter(input_it)
    while True:
        # resp=just_try(lambda: next(it),default=default,reraise=reraise,verbose=verbose)
        try:
            resp = next(it)
        except StopIteration:
            break
        except Exception as e:
            if verbose:
                print(f"\ntried and failed with: {e}\n")
                traceback.print_exc(file=sys.stderr)
            if break_on_failure:
                break
            else:
                resp = default

        yield resp


@beartype
def buffer_shuffle(
    data: Iterable[T], buffer_size: int, verbose: bool = False
) -> Iterator[T]:
    """
    based on : https://github.com/pytorch/pytorch/commit/96540e918c4ca3f0a03866b9d281c34c65bd76a4#diff-425b66e1ff01d191679c386258a7156dfb5aacd64a8e0947b24fbdebcbee8529
    """
    it = iter(data)
    start = time()
    buf = [next(it) for _ in range(buffer_size)]
    if verbose:
        print(f"filling shuffle-buffer of size {len(buf)} took: {time()-start} seconds")

    for x in it:
        idx = random.randint(0, buffer_size - 1)
        yield buf[idx]
        buf[idx] = x

    random.shuffle(buf)
    while buf:
        yield buf.pop()


def get_dict_paths(paths, root_path, my_dict):
    if not isinstance(my_dict, dict):
        paths.append(root_path)
        return root_path
    for k, v in my_dict.items():
        path = root_path + [k]
        get_dict_paths(paths, path, v)


class Singleton(type):
    """
    see: https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


@dataclass
class _NOT_EXISTING(metaclass=Singleton):
    pass


NOT_EXISTING = _NOT_EXISTING()


@beartype
def get_val_from_nested_dict(d: dict, path: list[str]) -> Union[Any, _NOT_EXISTING]:
    for key in path:
        if key in d.keys():
            d = d[key]
        else:
            d = NOT_EXISTING
            break
    return d


@dataclass
class TimedIterable(Generic[T]):
    iterable: Iterable[T]
    duration: float = field(default=0.0, init=False)
    outcome: float = field(default=0.0, init=False)
    # overall_duration_only:bool
    weight_fun: Callable[[Any], float] = lambda x: 1.0

    def __iter__(self) -> Iterator[T]:
        last_time = time()
        for x in self.iterable:
            self.duration += time() - last_time
            self.outcome += self.weight_fun(x)
            yield x
            last_time = time()

    @property
    def speed(self):
        return self.outcome / self.duration
