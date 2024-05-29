# -*- coding: utf-8 -*-
from anytree import AnyNode, LoopError, NodeMixin, PostOrderIter, PreOrderIter, TreeError, TypedNode

import pytest
from pytest_mock import mocker, MockerFixture


def test_parent_child():
    """A tree parent and child attributes."""
    root = TypedNode()
    s0 = TypedNode(parent=root)
    s0b = TypedNode(parent=s0)
    s0a = TypedNode(parent=s0)
    s1 = TypedNode(parent=root)
    s1a = TypedNode(parent=s1)
    s1b = TypedNode(parent=s1)
    s1c = TypedNode(parent=s1)
    s1ca = TypedNode(parent=s1c)

    del root.parent

    assert root.parent is None
    assert root.children == [s0, s1]
    assert s0.parent == root
    assert s0.children == [s0b, s0a]
    assert s0b.parent == s0
    assert s0b.children == []
    assert s0a.parent == s0
    assert s0a.children == []
    assert s1.parent == root
    assert s1.children == [s1a, s1b, s1c]
    assert s1a.parent == s1
    assert s1a.children == []
    assert s1b.parent == s1
    assert s1b.children == []
    assert s1c.parent == s1
    assert s1c.children == [s1ca]
    assert s1ca.parent == s1c
    assert s1ca.children == []

    # change parent
    s1ca.parent = s0

    assert root.parent is None
    assert root.children == [s0, s1]
    assert s0.parent == root
    assert s0.children == [s0b, s0a, s1ca]
    assert s0b.parent == s0
    assert s0b.children == []
    assert s0a.parent == s0
    assert s0a.children == []
    assert s1.parent == root
    assert s1.children == [s1a, s1b, s1c]
    assert s1a.parent == s1
    assert s1a.children == []
    assert s1b.parent == s1
    assert s1b.children == []
    assert s1c.parent == s1
    assert s1c.children == []
    assert s1ca.parent == s0
    assert s1ca.children == []

    # break tree into two
    del s1.parent

    assert root.parent is None
    assert root.children == [s0]
    assert s0.parent == root
    assert s0.children == [s0b, s0a, s1ca]
    assert s0b.parent == s0
    assert s0b.children == []
    assert s0a.parent == s0
    assert s0a.children == []
    assert s1.parent is None
    assert s1.children == [s1a, s1b, s1c]
    assert s1a.parent == s1
    assert s1a.children == []
    assert s1b.parent == s1
    assert s1b.children == []
    assert s1c.parent == s1
    assert s1c.children == []
    assert s1ca.parent == s0
    assert s1ca.children == []

    # set to the same
    s1b.parent = s1

    assert root.parent is None
    assert root.children == [s0]
    assert s0.parent == root
    assert s0.children == [s0b, s0a, s1ca]
    assert s0b.parent == s0
    assert s0b.children == []
    assert s0a.parent == s0
    assert s0a.children == []
    assert s1.parent is None
    assert s1.children == [s1a, s1b, s1c]
    assert s1a.parent == s1
    assert s1a.children == []
    assert s1b.parent == s1
    assert s1b.children == []
    assert s1c.parent == s1
    assert s1c.children == []
    assert s1ca.parent == s0
    assert s1ca.children == []

    del s1a.parent

    assert s1a.parent is None


def test_detach_children():

    root = TypedNode()
    s0 = TypedNode(parent=root)
    s0b = TypedNode(parent=s0)
    s0a = TypedNode(parent=s0)
    s1 = TypedNode(parent=root)
    s1a = TypedNode(parent=s1)
    s1b = TypedNode(parent=s1)
    s1c = TypedNode(parent=s1)
    s1ca = TypedNode(parent=s1c)

    assert root.descendants == [s0, s0b, s0a, s1, s1a, s1b, s1c, s1ca]
    del s0.children
    assert root.descendants == [s0, s1, s1a, s1b, s1c, s1ca]
    del s1.children
    assert root.descendants == [s0, s1]


def test_children_setter():

    root = TypedNode()
    s0 = TypedNode()
    s1 = TypedNode()
    s0a = TypedNode()

    root.children = [s0, s1]
    s0.children = [s0a]
    assert root.descendants == [s0, s0a, s1]

    with pytest.raises(LoopError):
        s0.children = [s0]

    # test whether tree is unchanged after LoopError
    assert root.descendants == [s0, s0a, s1]

    # with assert_raises(LoopError, "Cannot set parent. Node('/root/sub0') is parent of Node('/root/sub0/sub0B')."):
    with pytest.raises(LoopError):
        s0a.children = [s0]

    # test whether tree is unchanged after LoopError
    assert root.descendants == [s0, s0a, s1]

    root.children = [s0, s1]
    s0.children = [s0a]
    s0a.children = [s1]
    assert root.descendants == [s0, s0a, s1]


def test_children_setter_large():

    root = TypedNode()
    s0 = TypedNode()
    s0b = TypedNode()
    s0a = TypedNode()
    s1 = TypedNode()
    s1a = TypedNode()
    s1b = TypedNode()
    s1c = TypedNode()

    root.children = [s0, s1]
    assert root.descendants == [s0, s1]
    s0.children = [s0a, s0b]
    assert root.descendants == [s0, s0a, s0b, s1]
    s1.children = [s1a, s1b, s1c]
    assert root.descendants == [s0, s0a, s0b, s1, s1a, s1b, s1c]


def test_node_children_multiple():

    root = TypedNode()
    sub = TypedNode()
    # with assert_raises(TreeError, "Cannot add node Node('/sub') multiple times as child."):
    with pytest.raises(TreeError):
        root.children = [sub, sub]


def test_recursion_detection():
    """Recursion detection."""
    root = TypedNode()
    s0 = TypedNode(parent=root)
    TypedNode(parent=s0)
    s0a = TypedNode(parent=s0)

    # try recursion
    assert root.parent is None
    with pytest.raises(LoopError):
        root.parent = root
    assert root.parent is None

    with pytest.raises(LoopError):
        root.parent = s0a
    assert root.parent is None

    assert s0.parent is root
    with pytest.raises(LoopError):
        s0.parent = s0a
    assert s0.parent is root


def test_ancestors():
    """Node.ancestors."""
    root = TypedNode()
    s0 = TypedNode(parent=root)
    s0b = TypedNode(parent=s0)
    s0a = TypedNode(parent=s0)
    s1 = TypedNode(parent=root)
    s1c = TypedNode(parent=s1)
    s1ca = TypedNode(parent=s1c)

    assert root.ancestors == []
    assert s0.ancestors == [root]
    assert s0b.ancestors == [root, s0]
    assert s0a.ancestors == [root, s0]
    assert s1ca.ancestors == [root, s1, s1c]


def test_node_children_init():
    """Node With Children Attribute."""
    c1_1 = TypedNode()
    c1 = TypedNode(children=[c1_1])
    c2 = TypedNode()

    root = TypedNode(children=[c1, c2])

    assert root.children == [c1, c2]
    assert c1.children == [c1_1]


# def test_anynode_children_init():
#     """Anynode With Children Attribute."""
#     root = AnyNode(foo="root", children=[AnyNode(foo="a", children=[AnyNode(foo="aa")]), AnyNode(foo="b")])
#     assert repr(root.descendants) == "(AnyNode(foo='a'), AnyNode(foo='aa'), AnyNode(foo='b'))"


def test_descendants():
    """Node.descendants."""
    root = TypedNode()
    s0 = TypedNode(parent=root)
    s0b = TypedNode(parent=s0)
    s0a = TypedNode(parent=s0)
    s1 = TypedNode(parent=root)
    s1c = TypedNode(parent=s1)
    s1ca = TypedNode(parent=s1c)

    assert root.descendants == [s0, s0b, s0a, s1, s1c, s1ca]
    assert s1.descendants == [s1c, s1ca]
    assert s1c.descendants == [s1ca]
    assert s1ca.descendants == []


def test_root():
    """Node.root."""
    root = TypedNode()
    s0 = TypedNode(parent=root)
    s0b = TypedNode(parent=s0)
    s0a = TypedNode(parent=s0)
    s1 = TypedNode(parent=root)
    s1c = TypedNode(parent=s1)
    s1ca = TypedNode(parent=s1c)

    assert root.root == root
    assert s0.root == root
    assert s0b.root == root
    assert s0a.root == root
    assert s1.root == root
    assert s1c.root == root
    assert s1ca.root == root


def test_siblings():
    """Node.siblings."""
    root = TypedNode()
    s0 = TypedNode(parent=root)
    s0b = TypedNode(parent=s0)
    s0a = TypedNode(parent=s0)
    s1 = TypedNode(parent=root)
    s1c = TypedNode(parent=s1)
    s1ca = TypedNode(parent=s1c)

    assert root.siblings == []
    assert s0.siblings == [s1]
    assert s0b.siblings == [s0a]
    assert s0a.siblings == [s0b]
    assert s1.siblings == [s0]
    assert s1c.siblings == []
    assert s1ca.siblings == []


def test_is_leaf():
    """Node.is_leaf."""
    root = TypedNode()
    s0 = TypedNode(parent=root)
    s0b = TypedNode(parent=s0)
    s0a = TypedNode(parent=s0)
    s1 = TypedNode(parent=root)
    s1c = TypedNode(parent=s1)
    s1ca = TypedNode(parent=s1c)

    assert root.is_leaf is False
    assert s0.is_leaf is False
    assert s0b.is_leaf is True
    assert s0a.is_leaf is True
    assert s1.is_leaf is False
    assert s1c.is_leaf is False
    assert s1ca.is_leaf is True


def test_leaves():
    """Node.leaves."""
    root = TypedNode()
    s0 = TypedNode(parent=root)
    s0b = TypedNode(parent=s0)
    s0a = TypedNode(parent=s0)
    s1 = TypedNode(parent=root)
    s1c = TypedNode(parent=s1)
    s1ca = TypedNode(parent=s1c)

    assert root.leaves == [s0b, s0a, s1ca]
    assert s0.leaves == [s0b, s0a]
    assert s0b.leaves == [s0b]
    assert s0a.leaves == [s0a]
    assert s1.leaves == [s1ca]
    assert s1c.leaves == [s1ca]
    assert s1ca.leaves == [s1ca]


def test_is_root():
    """Node.is_root."""
    root = TypedNode()
    s0 = TypedNode(parent=root)
    s0b = TypedNode(parent=s0)
    s0a = TypedNode(parent=s0)
    s1 = TypedNode(parent=root)
    s1c = TypedNode(parent=s1)
    s1ca = TypedNode(parent=s1c)

    assert root.is_root is True
    assert s0.is_root is False
    assert s0b.is_root is False
    assert s0a.is_root is False
    assert s1.is_root is False
    assert s1c.is_root is False
    assert s1ca.is_root is False


def test_height():
    """Node.height."""
    root = TypedNode()
    s0 = TypedNode(parent=root)
    s0b = TypedNode(parent=s0)
    s0a = TypedNode(parent=s0)
    s1 = TypedNode(parent=root)
    s1c = TypedNode(parent=s1)
    s1ca = TypedNode(parent=s1c)

    assert root.height == 3
    assert s0.height == 1
    assert s0b.height == 0
    assert s0a.height == 0
    assert s1.height == 2
    assert s1c.height == 1
    assert s1ca.height == 0


def test_size():
    """Node.size."""
    root = TypedNode()
    s0 = TypedNode(parent=root)
    s0b = TypedNode(parent=s0)
    s0a = TypedNode(parent=s0)
    s1 = TypedNode(parent=root)
    s1c = TypedNode(parent=s1)
    s1ca = TypedNode(parent=s1c)

    assert root.size == 7
    assert s0.size == 3
    assert s0b.size == 1
    assert s0a.size == 1
    assert s1.size == 3
    assert s1c.size == 2
    assert s1ca.size == 1


def test_depth():
    """Node.depth."""
    root = TypedNode()
    s0 = TypedNode(parent=root)
    s0b = TypedNode(parent=s0)
    s0a = TypedNode(parent=s0)
    s1 = TypedNode(parent=root)
    s1c = TypedNode(parent=s1)
    s1ca = TypedNode(parent=s1c)

    assert root.depth == 0
    assert s0.depth == 1
    assert s0b.depth == 2
    assert s0a.depth == 2
    assert s1.depth == 1
    assert s1c.depth == 2
    assert s1ca.depth == 3


def test_parent():
    """Parent attribute."""
    foo = TypedNode()
    assert foo.parent is None


def test_pre_order_iter():
    """Pre-Order Iterator."""
    f = TypedNode()
    b = TypedNode(parent=f)
    a = TypedNode(parent=b)
    d = TypedNode(parent=b)
    c = TypedNode(parent=d)
    e = TypedNode(parent=d)
    g = TypedNode(parent=f)
    i = TypedNode(parent=g)
    h = TypedNode(parent=i)

    assert [node for node in PreOrderIter(f)] == [f, b, a, d, c, e, g, i, h]


def test_post_order_iter():
    """Post-Order Iterator."""
    f = TypedNode()
    b = TypedNode(parent=f)
    a = TypedNode(parent=b)
    d = TypedNode(parent=b)
    c = TypedNode(parent=d)
    e = TypedNode(parent=d)
    g = TypedNode(parent=f)
    i = TypedNode(parent=g)
    h = TypedNode(parent=i)

    assert [node for node in PostOrderIter(f)] == [a, c, e, d, b, h, i, g, f]


# def test_anyname():
#     """Support any type as name."""
#     myroot = TypedNode([1, 2, 3])
#     TypedNode(parent=myroot)
#     assert str(myroot) == "Node('/[1, 2, 3]')"


# def test_hookups(mocker: MockerFixture):
#     """Hookup attributes #29."""

#     class MyNode(TypedNode):
#         def _pre_attach(self, parent):
#             pass
#             # assert self.parent is None
#             # assert self.children == tuple()
#             # assert str(self.path) == "(MyNode('/B'),)"

#         def _post_attach(self, parent):
#             # assert str(self.parent) == "MyNode('/A')"
#             # assert self.children == tuple()
#             # assert str(self.path) == "(MyNode('/A'), MyNode('/A/B'))"
#             pass

#         def _pre_detach(self, parent):
#             # assert str(self.parent) == "MyNode('/A')"
#             # assert self.children == tuple()
#             # assert str(self.path) == "(MyNode('/A'), MyNode('/A/B'))"
#             pass

#         def _post_detach(self, parent):
#             # assert str(self.parent) == "None"
#             # assert self.children == tuple()
#             # assert str(self.path) == "(MyNode('/B'),)"
#             pass

#     node_a = MyNode()
#     node_b = mocker.MagicMock(MyNode)(node_a)

#     # node_b = MyNode(node_a)  # attach B on A

#     node_b._pre_attach.assert_called_once()

#     # node_b.parent = None  # detach B from A
#     del node_b.parent  # detach B from A


def test_eq_overwrite():
    """Node with overwritten __eq__."""

    class EqOverwrittingNode(TypedNode):
        def __init__(self, a, b, parent=None):
            super(EqOverwrittingNode, self).__init__(parent)
            self.a = a
            self.b = b

        def __eq__(self, other: "EqOverwrittingNode"):
            return self.a == other.a and self.b == other.b
            # if isinstance(other, EqOverwrittingNode):
            # else:
            #     return NotImplemented

    r = EqOverwrittingNode(0, 0)
    a = EqOverwrittingNode(1, 0, parent=r)
    b = EqOverwrittingNode(1, 0, parent=r)
    assert a.parent is r
    assert b.parent is r
    assert a.a == 1
    assert a.b == 0
    assert b.a == 1
    assert b.b == 0
