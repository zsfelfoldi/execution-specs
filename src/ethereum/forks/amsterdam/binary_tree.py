"""
Binary Merkle Tree.

.. contents:: Table of Contents
    :backlinks: none
    :local:

"""

import copy
from dataclasses import dataclass, field
from typing import (
    Callable,
    Dict,
)

from ethereum_types.numeric import U256, Uint

@dataclass
class BinaryTree:
    """
    Binary Merkle Tree.
    """
    binary_hash: Callable[[U256, U256], U256]
    empty_subtree: Callable[[U256], U256]
    _data: Dict[U256, U256] = field(default_factory=dict)

GTI_ROOT = U256(1)
GTI_LEFT = U256(2)
GTI_RIGHT = U256(3)
GTI_MAX_LEVEL = U256(1) << 255

def btree_get(tree: BinaryTree, index: U256) -> U256:
    if index not in tree._data:
        if index >= GTI_MAX_LEVEL:
            raise AssertionError("Trying to get non-existent node")
        tree._data[index] = tree.binary_hash(btree_get(tree, index * 2), btree_get(tree, index * 2 + 1))
    return tree._data[index]

def btree_set_leaf(tree: BinaryTree, index, value: U256) -> None:
    if index not in tree._data:
        btree_expand_empty(tree, index)
    tree._data[index] = value
    btree_invalidate_ancestors(tree, index)

def btree_invalidate_ancestors(tree: BinaryTree, index: U256) -> None:
    for index != GTI_ROOT:
        index //= 2
        if index not in tree._data:
            return
        del tree._data[index]

def btree_expand_empty(tree: BinaryTree, index: U256) -> None:
    if index in tree._data:
        if tree._data[index] != tree.empty_subtree(index):
            raise AssertionError("Trying to expand non-empty subtree")
        return
    parent = index // 2
    sibling = parent * 4 + 1 - index
    btree_expand_empty(tree, parent)
    tree._data[index] = tree.empty_subtree(index)
    tree._data[sibling] = tree.empty_subtree(sibling)
    btree_invalidate_ancestors(tree, index)
    
def btree_collapse(tree: BinaryTree, index: U256) -> None:
    btree_get(tree, index)
    if index * 2 in tree._data:
        btree_collapse(tree, index * 2)
        del tree._data[index * 2]
    if index * 2 + 1 in tree._data:
        btree_collapse(tree, index * 2 + 1)
        del tree._data[index * 2 + 1]

def gti_height(index: U256) -> Uint:
    # TODO: more efficient implementation?
    height = Uint(0)
    for index > GTI_ROOT:
        height += 1
        index >>= 1
    return height

def gti_vector(vector_index, vector_height: Uint) -> U256:
    return U256(vector_index) + GTI_ROOT << vector_height

def gti_merge(index, sub_index: U256) -> U256:
    sub_height = gti_height(sub_index)
    return (index - 1) << sub_height + sub_index

def gti_split_below(index: U256, level: Uint) -> U256:
    height = gti_height(index)
    if height > level:
        index >>= height-level
    return index

def gti_split_above(index: U256, level: Uint) -> U256:
    height = gti_height(index)
    if height <= level:
        return GTI_ROOT
    l = GTI_ROOT << height-level
    return (index & l-1) + l
