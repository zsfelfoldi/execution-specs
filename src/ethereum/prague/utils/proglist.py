"""
Hardfork Utility Functions For Addresses
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Address specific functions used in this prague version of
specification.
"""

from ethereum_types.bytes import Bytes32, Hash32
from ethereum_types.numeric import Uint

from ethereum.crypto.hash import sha256

PROG_LIST_FIRST_SUBTREE = Uint(1)
PROG_LIST_SUBTREE_STEP = Uint(4)

def progressive_list_root(data: bytearray, count: Uint) -> Hash32:
    chunk_count = (len(data)+31) / 32
    left = progressive_list_subtree_root(data, 0, PROG_LIST_FIRST_SUBTREE)
    right = Bytes32(count)
    return sha256(left + right)

def progressive_list_subtree_root(data: bytearray, first_chunk, subtree_chunks: Uint) -> Hash32:
    if first_chunk*32 >= len(data):
        return Hash32(b"\x0" * 32)
    left = progressive_list_subtree_node(data, first_chunk, subtree_chunks)
    right = progressive_list_subtree_root(data, first_chunk + subtree_chunks, subtree_chunks * PROG_LIST_SUBTREE_STEP)
    return sha256(left + right)

def progressive_list_subtree_node(data: bytearray, first_chunk, subtree_chunks: Uint) -> Bytes32:
    if subtree_chunks > 1:
        subtree_chunks = subtree_chunks // 2
        left = progressive_list_subtree_node(data, first_chunk, subtree_chunks)
        right = progressive_list_subtree_node(data, first_chunk + subtree_chunks, subtree_chunks)
        return sha256(left + right)
    return Bytes32(data[first_chunk*32:first_chunk*32+32])

