import dataclasses
from typing import Annotated, TypeVar

from beartype.vale import IsAttr, IsEqual, Is
from numpy import floating, int16, number
from numpy.typing import NDArray

NumpyArray = NDArray[number]
NumpyFloat2DArray = Annotated[NDArray[floating], IsAttr["ndim", IsEqual[2]]]
NumpyFloat1DArray = Annotated[NDArray[floating], IsAttr["ndim", IsEqual[1]]]
# TODO: rename to NumpyFloatDim1, NumpyFloat32Dim1, etc
Numpy1DArray = Annotated[NDArray[number], IsAttr["ndim", IsEqual[1]]]
NumpyInt16Dim1 = Annotated[NDArray[int16], IsAttr["ndim", IsEqual[1]]]

NeStr = Annotated[str, Is[lambda s: len(s) > 0]]
Dataclass = Annotated[object, Is[lambda o: dataclasses.is_dataclass(o)]]
# TODO: Annotated[object,...] is NOT working!
# StrOrBytesInstance = Annotated[object, IsInstance[str]]

T = TypeVar("T")

NeList = Annotated[list[T], Is[lambda lst: len(lst) > 0]]
# NotNone = Annotated[Any, Is[lambda x:x is None]] # TODO: not working!

try:
    import torch

    TorchTensor3D = Annotated[torch.Tensor, IsAttr["ndim", IsEqual[3]]]
    TorchTensor2D = Annotated[torch.Tensor, IsAttr["ndim", IsEqual[2]]]
    TorchTensor1D = Annotated[torch.Tensor, IsAttr["ndim", IsEqual[1]]]
except Exception as e:
    print(f"no torch!")
