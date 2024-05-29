from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class MutualLink(Generic[T]):
    def __init__(self, left: T = None, right: T = None):
        self.__left: T = left
        self.__right: T = right

    @property
    def left(self) -> T:
        return self.__left

    @left.setter
    def left(self, left: T):
        self.__left = left

    @property
    def right(self) -> T:
        return self.__right

    @right.setter
    def right(self, right: T):
        self.__right = right

    @property
    def has_left(self) -> bool:
        return self.__left is not None

    @property
    def has_right(self) -> bool:
        return self.__right is not None
