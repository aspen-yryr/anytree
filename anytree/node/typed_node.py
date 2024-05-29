# -*- coding: utf-8 -*-

from typing import Generic, Optional, TypeVar
import warnings

from pydantic import BaseModel

from anytree.iterators import PreOrderIter

from ..config import ASSERTIONS
from .exceptions import LoopError, TreeError
from .lightnodemixin import LightNodeMixin
from .mutual_link import MutualLink

T = TypeVar("T", bound=BaseModel)


class TypedNode(Generic[T]):
    def __init__(
        self, value: T, parent: Optional["TypedNode[T]"] = None, children: Optional[list["TypedNode[T]"]] = None
    ):
        self.value = value
        self.__parent_link: Optional[MutualLink["TypedNode[T]"]] = None
        self.__child_links: list[MutualLink["TypedNode[T]"]] = []

        if parent is not None:
            self.parent = parent

        if children is not None:
            self.children = children

    @property
    def parent(self) -> Optional["TypedNode[T]"]:
        return self.__parent_link.left if self.__parent_link is not None else None

    @parent.setter
    def parent(self, parent: "TypedNode[T]"):
        self.__check_loop(parent)
        if self.parent is not parent:
            self.__detach()
            self.__attach(parent)

    @parent.deleter
    def parent(self):
        if self.parent is not None:
            self.__detach()

    def __check_loop(self, parent: "TypedNode[T]"):
        if parent is self:
            msg = "Cannot set parent. %r cannot be parent of itself."
            raise LoopError(msg % (self,))
        if any(pc is self for pc in parent.ancestors):
            msg = "Cannot set parent. %r is parent of %r."
            raise LoopError(msg % (self, parent))

    def __detach(self):
        if self.__parent_link is None:
            return

        parent_link = self.__parent_link
        parent = parent_link.left
        assert parent is not None, "Tree is corrupt."

        self._pre_detach(parent)

        # ATOMIC START
        parent.__child_links.remove(parent_link)
        self.__parent_link = None
        # ATOMIC END

        self._post_detach(parent)

    def __attach(self, parent: "TypedNode[T]"):
        assert not any(child is self for child in parent.children), "Tree is corrupt."
        self._pre_attach(parent)

        new_link = MutualLink(left=parent, right=self)

        # ATOMIC START
        self.__parent_link = new_link
        parent.__child_links.append(new_link)
        # ATOMIC END

        self._post_attach(parent)

    @property
    def children(self):
        return list(filter(lambda x: x is not None, [link.right for link in self.__child_links]))

    @staticmethod
    def __check_children(children: list["TypedNode[T]"]):
        seen = set()
        for child in children:
            childid = id(child)
            if childid not in seen:
                seen.add(childid)
            else:
                msg = "Cannot add node %r multiple times as child." % (child,)
                raise TreeError(msg)

    @children.setter
    def children(self, children: list["TypedNode[T]"]):
        TypedNode.__check_children(children)

        # ATOMIC start
        for child in children:
            child.__check_loop(self)

        self._pre_attach_children(children)
        for child in children:
            child.parent = self
        self._post_attach_children(children)
        assert len(self.children) == len(children)

    @children.deleter
    def children(self):
        children = self.children
        self._pre_detach_children(children)
        for child in self.children:
            del child.parent
        self._post_detach_children(children)

    def _pre_detach_children(self, children: list["TypedNode[T]"]) -> None:
        """Method call before detaching `children`."""

    def _post_detach_children(self, children: list["TypedNode[T]"]) -> None:
        """Method call after detaching `children`."""

    def _pre_attach_children(self, children: list["TypedNode[T]"]) -> None:
        """Method call before attaching `children`."""

    def _post_attach_children(self, children: list["TypedNode[T]"]) -> None:
        """Method call after attaching `children`."""

    @property
    def path(self):
        """
        Path from root node down to this `Node`.

        >>> from anytree import Node
        >>> udo = Node("Udo")
        >>> marc = Node("Marc", parent=udo)
        >>> lian = Node("Lian", parent=marc)
        >>> udo.path
        (Node('/Udo'),)
        >>> marc.path
        (Node('/Udo'), Node('/Udo/Marc'))
        >>> lian.path
        (Node('/Udo'), Node('/Udo/Marc'), Node('/Udo/Marc/Lian'))
        """
        return self._path

    def iter_path_reverse(self):
        """
        Iterate up the tree from the current node to the root node.

        >>> from anytree import Node
        >>> udo = Node("Udo")
        >>> marc = Node("Marc", parent=udo)
        >>> lian = Node("Lian", parent=marc)
        >>> for node in udo.iter_path_reverse():
        ...     print(node)
        Node('/Udo')
        >>> for node in marc.iter_path_reverse():
        ...     print(node)
        Node('/Udo/Marc')
        Node('/Udo')
        >>> for node in lian.iter_path_reverse():
        ...     print(node)
        Node('/Udo/Marc/Lian')
        Node('/Udo/Marc')
        Node('/Udo')
        """
        node = self
        while node is not None:
            yield node
            node = node.parent

    @property
    def _path(self) -> list["TypedNode[T]"]:
        return list(reversed(list(self.iter_path_reverse())))

    @property
    def ancestors(self) -> list["TypedNode[T]"]:
        """
        All parent nodes and their parent nodes.

        >>> from anytree import Node
        >>> udo = Node("Udo")
        >>> marc = Node("Marc", parent=udo)
        >>> lian = Node("Lian", parent=marc)
        >>> udo.ancestors
        ()
        >>> marc.ancestors
        (Node('/Udo'),)
        >>> lian.ancestors
        (Node('/Udo'), Node('/Udo/Marc'))
        """
        if self.parent is None:
            return []
        return self.parent.path

    @property
    def descendants(self) -> list["TypedNode[T]"]:
        """
        All child nodes and all their child nodes.

        >>> from anytree import Node
        >>> udo = Node("Udo")
        >>> marc = Node("Marc", parent=udo)
        >>> lian = Node("Lian", parent=marc)
        >>> loui = Node("Loui", parent=marc)
        >>> soe = Node("Soe", parent=lian)
        >>> udo.descendants
        (Node('/Udo/Marc'), Node('/Udo/Marc/Lian'), Node('/Udo/Marc/Lian/Soe'), Node('/Udo/Marc/Loui'))
        >>> marc.descendants
        (Node('/Udo/Marc/Lian'), Node('/Udo/Marc/Lian/Soe'), Node('/Udo/Marc/Loui'))
        >>> lian.descendants
        (Node('/Udo/Marc/Lian/Soe'),)
        """
        return list(PreOrderIter(self))[1:]

    @property
    def root(self) -> "TypedNode[T]":
        """
        Tree Root Node.

        >>> from anytree import Node
        >>> udo = Node("Udo")
        >>> marc = Node("Marc", parent=udo)
        >>> lian = Node("Lian", parent=marc)
        >>> udo.root
        Node('/Udo')
        >>> marc.root
        Node('/Udo')
        >>> lian.root
        Node('/Udo')
        """
        node = self
        while node.parent is not None:
            node = node.parent
        return node

    @property
    def siblings(self) -> list["TypedNode[T]"]:
        if self.parent is None:
            return []
        return list(node for node in self.parent.children if node is not self)

    @property
    def leaves(self) -> list["TypedNode[T]"]:
        return list(PreOrderIter(self, filter_=lambda node: node.is_leaf))

    @property
    def is_leaf(self) -> bool:
        """
        `Node` has no children (External Node).

        >>> from anytree import Node
        >>> udo = Node("Udo")
        >>> marc = Node("Marc", parent=udo)
        >>> lian = Node("Lian", parent=marc)
        >>> udo.is_leaf
        False
        >>> marc.is_leaf
        False
        >>> lian.is_leaf
        True
        """
        return len(self.children) == 0

    @property
    def is_root(self) -> bool:
        return self.parent is None

    @property
    def height(self) -> int:
        """
        Number of edges on the longest path to a leaf `Node`.

        >>> from anytree import Node
        >>> udo = Node("Udo")
        >>> marc = Node("Marc", parent=udo)
        >>> lian = Node("Lian", parent=marc)
        >>> udo.height
        2
        >>> marc.height
        1
        >>> lian.height
        0
        """
        if len(self.children) == 0:
            return 0
        else:
            return max(child.height for child in self.children) + 1

    @property
    def depth(self):
        """
        Number of edges to the root `Node`.

        >>> from anytree import Node
        >>> udo = Node("Udo")
        >>> marc = Node("Marc", parent=udo)
        >>> lian = Node("Lian", parent=marc)
        >>> udo.depth
        0
        >>> marc.depth
        1
        >>> lian.depth
        2
        """
        # count without storing the entire path
        # pylint: disable=W0631
        for depth, _ in enumerate(self.iter_path_reverse()):
            continue
        return depth

    @property
    def size(self):
        """
        Tree size --- the number of nodes in tree starting at this node.

        >>> from anytree import Node
        >>> udo = Node("Udo")
        >>> marc = Node("Marc", parent=udo)
        >>> lian = Node("Lian", parent=marc)
        >>> loui = Node("Loui", parent=marc)
        >>> soe = Node("Soe", parent=lian)
        >>> udo.size
        5
        >>> marc.size
        4
        >>> lian.size
        2
        >>> loui.size
        1
        """
        # count without storing the entire path
        # pylint: disable=W0631
        for size, _ in enumerate(PreOrderIter(self), 1):
            continue
        return size

    def _pre_detach(self, parent: "TypedNode[T]"):
        """Method call before detaching from `parent`."""

    def _post_detach(self, parent: "TypedNode[T]"):
        """Method call after detaching from `parent`."""

    def _pre_attach(self, parent: "TypedNode[T]"):
        """Method call before attaching to `parent`."""

    def _post_attach(self, parent: "TypedNode[T]"):
        """Method call after attaching to `parent`."""
