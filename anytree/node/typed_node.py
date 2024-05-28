# -*- coding: utf-8 -*-

from typing import Optional
import warnings

from anytree.iterators import PreOrderIter

from ..config import ASSERTIONS
from .exceptions import LoopError, TreeError
from .lightnodemixin import LightNodeMixin


class TypedNode:

    separator = "/"

    def __init__(self, parent: Optional["TypedNode"] = None, children: Optional[list["TypedNode"]] = None):
        self.__parent: Optional["TypedNode"] = None
        self.__children: list["TypedNode"] = []

        if parent is not None:
            self.parent = parent

        if children is not None:
            self.children = children

    @property
    def parent(self) -> Optional["TypedNode"]:
        return self.__parent

    @parent.setter
    def parent(self, value: "TypedNode"):
        if self.__parent is not value:
            self.__check_loop(value)
            if self.__parent is not None:
                self.__detach(self.__parent)
            self.__attach(value)

    @parent.deleter
    def parent(self):
        if self.__parent is not None:
            self.__detach(self.__parent)

    def __check_loop(self, node: "TypedNode"):
        if node is self:
            msg = "Cannot set parent. %r cannot be parent of itself."
            raise LoopError(msg % (self,))
        if any(child is self for child in node.iter_path_reverse()):
            msg = "Cannot set parent. %r is parent of %r."
            raise LoopError(msg % (self, node))

    def __detach(self, parent: "TypedNode"):
        self._pre_detach(parent)

        # ATOMIC START
        parent.__children = [child for child in parent.children if child is not self]
        self.__parent = None
        # ATOMIC END

        self._post_detach(parent)

    def __attach(self, parent: "TypedNode"):
        assert not any(child is self for child in parent.children), "Tree is corrupt."
        self._pre_attach(parent)

        # ATOMIC START
        parent.__children.append(self)
        self.__parent = parent
        # ATOMIC END

        self._post_attach(parent)

    @property
    def children(self):
        return self.__children

    # def __append_child(self, child: "TypedNode"):
    #     self.__children.append(child)
    #     child.__parent = self

    @staticmethod
    def __check_children(children: list["TypedNode"]):
        seen = set()
        for child in children:
            childid = id(child)
            if childid not in seen:
                seen.add(childid)
            else:
                msg = "Cannot add node %r multiple times as child." % (child,)
                raise TreeError(msg)

    @children.setter
    def children(self, children: list["TypedNode"]):
        TypedNode.__check_children(children)

        # ATOMIC start
        old_children = self.__children
        del self.children
        try:
            self._pre_attach_children(children)
            for child in children:
                child.parent = self
            self._post_attach_children(children)
            assert len(self.__children) == len(children)
        except Exception:
            self.children = old_children
            raise
        # ATOMIC end

    @children.deleter
    def children(self):
        children = self.children
        self._pre_detach_children(children)
        for child in self.children:
            del child.parent
        self._post_detach_children(children)

    def _pre_detach_children(self, children: list["TypedNode"]) -> None:
        """Method call before detaching `children`."""

    def _post_detach_children(self, children: list["TypedNode"]) -> None:
        """Method call after detaching `children`."""

    def _pre_attach_children(self, children: list["TypedNode"]) -> None:
        """Method call before attaching `children`."""

    def _post_attach_children(self, children: list["TypedNode"]) -> None:
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
    def _path(self) -> list["TypedNode"]:
        return list(reversed(list(self.iter_path_reverse())))

    @property
    def ancestors(self) -> list["TypedNode"]:
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
    def descendants(self) -> list["TypedNode"]:
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
    def root(self) -> "TypedNode":
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
    def siblings(self) -> list["TypedNode"]:
        if self.parent is None:
            return []
        return list(node for node in self.parent.children if node is not self)

    @property
    def leaves(self) -> list["TypedNode"]:
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
        if len(self.__children) == 0:
            return 0
        else:
            return max(child.height for child in self.__children) + 1

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

    def _pre_detach(self, parent: "TypedNode"):
        """Method call before detaching from `parent`."""

    def _post_detach(self, parent: "TypedNode"):
        """Method call after detaching from `parent`."""

    def _pre_attach(self, parent: "TypedNode"):
        """Method call before attaching to `parent`."""

    def _post_attach(self, parent: "TypedNode"):
        """Method call after attaching to `parent`."""
