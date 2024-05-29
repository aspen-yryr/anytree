from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class MutualLink(Generic[T]):
    def __init__(self, left: T = None, right: T = None):
        self.__left: T = left
        self.__right: T = right

    @property
    def left(self) -> T:
        return self.__left

    @property
    def right(self) -> T:
        return self.__right
