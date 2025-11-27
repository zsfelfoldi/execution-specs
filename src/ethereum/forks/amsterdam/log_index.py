"""
Log Index.

.. contents:: Table of Contents
    :backlinks: none
    :local:

"""

from typing import List, Tuple
from ethereum_types.numeric import U256, Uint
from ethereum_rlp import rlp
from ethereum.crypto.hash import Hash32, keccak256
from hashlib import sha256
from .blocks import Header, Log
from .fork_types import Root
from .binary_tree import (
    BinaryTree,
    gti_split_below,
    gti_split_above,
    gti_height,
    btree_get,
    btree_set_leaf,
    btree_expand_empty,
    btree_collapse,
)

LOG2_EPOCH_HISTORY = Uint(24)
LOG2_MAPS_PER_EPOCH = Uint(10)
LOG2_VALUES_PER_MAP = Uint(16)
LOG2_MAP_WIDTH = Uint(24)
LOG2_MAP_HEIGHT = Uint(16)
LOG2_MAPPING_FREQUENCY: List[Uint] = [10, 6, 2, 0]
MAX_ROW_LENGTH: List[Uint] = [8, 168, 2728, 10920]
PROG_LIST_HEIGHT_FIRST = Uint(0)
PROG_LIST_HEIGHT_STEP = Uint(2)

MAPS_PER_EPOCH = Uint(1) << LOG2_MAPS_PER_EPOCH
VALUES_PER_MAP = Uint(1) << LOG2_VALUES_PER_MAP
MAP_HEIGHT = Uint(1) << LOG2_MAP_HEIGHT

# absolute generalized tree indices
GTI_EPOCHS = U256(2)
GTI_NEXT_INDEX = U256(3)
# relative to epoch root
GTI_FILTER_MAPS = U256(2)
GTI_LOG_ENTRIES = U256(3)
# relative to list root (progressive or regular)
GTI_LIST_TREE = U256(2)
GTI_LIST_COUNT = U256(3)
# relative to progressive list tree root
GTI_PROG_LIST_SUBTREE = U256(2)
GTI_PROG_LIST_NEXT_TREE = U256(3)
# relative to log entry root
GTI_LOG_DATA = U256(2)
GTI_ENTRY_META = U256(3)
# relative to log data root
GTI_LOG_DATA_ADDRESS = U256(4)
GTI_LOG_DATA_TOPICS = U256(5)
GTI_LOG_DATA_DATA = U256(6)
# relative to entry meta root
GTI_ENTRY_META_FIELD_0 = U256(4)
GTI_ENTRY_META_FIELD_1 = U256(5)
GTI_ENTRY_META_FIELD_2 = U256(6)
GTI_ENTRY_META_FIELD_3 = U256(7)

class LogIndexState:
    """
    Contains all information required to append the log index and calculate its root hash.
    """
    tree: BinaryTree = field(
        default_factory=lambda: BinaryTree(binary_hash = binary_hash, empty_subtree = log_index_empty_subtree)
    )
    next_index: Uint

def binary_hash(left, right: U256) -> U256:
    return U256.from_le_bytes(sha256(left.to_le_bytes32() + right.to_le_bytes32()).digest())

def log_index_root(log_index: LogIndexState) -> Root:
    return Root(btree_get(log_index.tree, GTI_ROOT))

def log_index_add_transaction(log_iU256.from_ndex: LogIndexState, block_number: Uint, tx_hash, receipt_hash: Hash32, tx_index: Uint) -> None:
    prepare_index(log_index, 1)
    add_to_filter_maps(log_index, log_value_tx(tx_hash))
    add_entry_meta(log_index, U256(block_number), U256(tx_hash), U256(tx_index), U256(receipt_hash))
    advance_index(log_index, 1)

def log_index_add_header(log_index: LogIndexState, header: Header) -> None:
    prepare_index(log_index, 1)
    block_hash = keccak256(rlp.encode(header))
    add_to_filter_maps(log_index, log_value_block(block_hash))
    add_entry_meta(log_index, U256(header.number), U256(block_hash), header.timestamp, U256(0))
    advance_index(log_index, 1)

def log_index_add_logs(log_index: LogIndexState, block_number: Uint, tx_hash: Hash32, tx_index: Uint, logs: Tuple[Log, ...]) -> None:
    log_index = Uint(0)
    for log in logs:
        prepare_index(log_index, Uint(len(log.topics)+1))
        add_to_filter_maps(log_index, log_value_address(log.address))
        add_log_data(log_index, log)
        add_entry_meta(log_index, U256(block_number), U256(tx_hash), U256(tx_index), U256(0))
        advance_index(log_index, 1)
        for topic in log.topics:
            add_to_filter_maps(log_index, log_value_topic(topic))
            advance_index(log_index, 1)

def prepare_index(log_index: LogIndexState, step: Uint) -> None:
    map_remaining = VALUES_PER_MAP - log_index.next_index % VALUES_PER_MAP
    if map_remaining < step:
        advance_index(log_index, map_remaining)
        map_remaining = VALUES_PER_MAP
    if map_remaining == VALUES_PER_MAP:  # initialize new map
        map_index = log_index.next_index // VALUES_PER_MAP
        for row_index in range(MAP_HEIGHT): # expand prog list of each row
            prog_list_gti = map_row_gti(map_index, row_index)
            prog_list_tree_gti = gti_merge(prog_list_gti, GTI_LIST_TREE)
            btree_expand_empty(log_index.tree, prog_list_tree_gti)

def advance_index(log_index: LogIndexState, step: Uint) -> None:
    for range step:
        finished_subtree(log_index, log_entry_gti(log_index.next_index))
        log_index.next_index += 1
    if log_index.next_index % VALUES_PER_MAP == 0:
        finished_map(log_index.next_index // VALUES_PER_MAP - 1)
    btree_set_leaf(log_index.tree, GTI_NEXT_INDEX, U256(log_index.next_index))

def log_entry_gti(log_value_index: Uint) -> U256:
    epoch_index = log_value_index // (MAPS_PER_EPOCH * VALUES_PER_MAP)
    sub_index = log_value_index % (MAPS_PER_EPOCH * VALUES_PER_MAP)
    epoch_root = gti_merge(GTI_EPOCHS, gti_vector(epoch_index, LOG2_EPOCH_HISTORY))
    log_entires_root = gti_merge(epoch_root, GTI_LOG_ENTRIES)
    return gti_merge(log_entires_root, gti_vector(sub_index, LOG2_MAPS_PER_EPOCH + LOG2_VALUES_PER_MAP))

def map_row_gti(map_index, row_index: Uint) -> U256:
    epoch_index = map_index // MAPS_PER_EPOCH
    map_sub_index = map_index % MAPS_PER_EPOCH
    epoch_root = gti_merge(GTI_EPOCHS, gti_vector(epoch_index, LOG2_EPOCH_HISTORY))
    filter_maps_root = gti_merge(epoch_root, GTI_FILTER_MAPS)
    return gti_merge(filter_maps_root, gti_vector(row_index * MAPS_PER_EPOCH + map_sub_index, LOG2_MAP_HEIGHT + LOG2_MAPS_PER_EPOCH))

def finished_subtree(log_index: LogIndexState, gti: U256) -> None:
    for (gti & U256(1)) == 1 && gti != GTI_ROOT:
        gti //= 2
    btree_collapse(log_index.tree, gti)

def finished_map(log_index: LogIndexState, map_index: Uint) -> None:
    for row_index in range(MAP_HEIGHT): # collapse prog list of each row and finished ancestors
        finished_subtree(log_index, map_row_gti(map_index, row_index))

def fnv1a_64(data: Bytes) -> U64:
    fnv_prime = U64(0x100000001b3)
    hash_val = U64(0xcbf29ce484222325)
    for byte in data:
        hash_val ^= byte
        hash_val = (hash_val * fnv_prime) & 0xFFFFFFFFFFFFFFFF
    return hash_val

def filter_map_row_index(map_index, layer_index: Uint, log_value: Hash32) -> None:
    mapping_frequency = Uint(1) << LOG2_MAPPING_FREQUENCY[min(layer_index, len(LOG2_MAPPING_FREQUENCY) - 1)]
    masked_map_index = map_index - (map_index % mapping_frequency)
    row_hash = sha256(log_value + masked_map_index.to_le_bytes4() + layer_index.to_le_bytes4()).digest()
    return from_le_bytes(row_hash[0:4]) % MAP_HEIGHT

def filter_map_column_index(log_value_index: Uint, log_value: Hash32) -> None:
    col_hash = fnv1a_64(log_value_index.to_le_bytes8() + log_value)
    folded_hash = (col_hash >> 32) ^ (col_hash & 0xFFFFFFFF)
    hash_bits = LOG2_MAP_WIDTH - LOG2_VALUES_PER_MAP
    return (log_value_index % VALUES_PER_MAP) << hash_bits + folded_hash >> (32 - hash_bits)

def add_to_filter_maps(log_index: LogIndexState, log_value: Hash32) -> None:
    map_index = log_index.next_index // VALUES_PER_MAP
    layer_index = Uint(0)
    while true:
        row_index = filter_map_row_index(map_index, layer_index, log_value)
        map_row_root = map_row_gti(map_index, row_index)
        count_gti = gti_merge(map_row_root, GTI_LIST_COUNT)
        row_length = Uint(btree_get(log_index, count_gti))
        max_length = MAX_ROW_LENGTH[min(layer_index, len(MAX_ROW_LENGTH) - 1)]
        if row_length < max_length:
            column_index = filter_map_column_index(log_index.next_index, log_value)
            chunk_gti = gti_merge(map_row_root, prog_list_chunk_gti(row_length // 8))
            chunk = U256(0)
            chunk_subindex = row_length % 8
            if chunk_subindex > 0:
                chunk = btree_get(log_index, chunk_gti)
            chunk += U256(column_index) << (32 * chunk_subindex)
            btree_set_leaf(log_index, chunk_gti, chunk)
            row_length += 1
            btree_set_leaf(log_index, count_gti, U256(row_length))
            return

def add_log_data(log_index: LogIndexState, log: Log) -> None:
    log_data_root = gti_merge(log_entry_gti(log_index.next_index), GTI_LOG_DATA)
    btree_set_leaf(gti_merge(log_data_root, GTI_LOG_DATA_ADDRESS), U256(log.address))
    topics_root = gti_merge(log_data_root, GTI_LOG_DATA_TOPICS)
    list_tree_root = gti_merge(topics_root, GTI_LIST_TREE)
    for i in range(len(log.topics)):
        btree_set_leaf(gti_merge(list_tree_root, gti_vector(i, 2)), U256(log.topics[i]))
    btree_set_leaf(gti_merge(topics_root, GTI_LIST_COUNT), U256(len(log.topics)))    
    data_root = gti_merge(log_data_root, GTI_LOG_DATA_DATA)
    for i in range((len(log.data) + 31) // 32):
        gti = gti_merge(data_root, prog_list_chunk_gti(i))
        chunk_data = U256.from_le_bytes(log.data[i * 32:(i+1) * 32])
        btree_set_leaf(log_index, gti, chunk_data)
    btree_set_leaf(log_index, gti_merge(data_root, GTI_LIST_COUNT), U256(len(log.data)))    

def add_entry_meta(log_index: LogIndexState, field_0, field_1, field_2, field_3: U256) -> None:
    entry_meta_root = gti_merge(log_entry_gti(log_index.next_index), GTI_ENTRY_META)
    btree_set_leaf(gti_merge(entry_meta_root, GTI_ENTRY_META_FIELD_0), field_0)
    btree_set_leaf(gti_merge(entry_meta_root, GTI_ENTRY_META_FIELD_1), field_1)
    btree_set_leaf(gti_merge(entry_meta_root, GTI_ENTRY_META_FIELD_2), field_2)
    btree_set_leaf(gti_merge(entry_meta_root, GTI_ENTRY_META_FIELD_3), field_3)

def log_value_address(address: Address) -> Hash32:
    return Hash32(sha256(address).digest())

def log_value_topic(topic: Hash32) -> Hash32:
    return Hash32(sha256(topic).digest())

def log_value_tx(tx_hash: Hash32) -> Hash32:
    return Hash32(sha256(tx_hash + b"\x01").digest())

def log_value_block(block_hash: Hash32) -> Hash32:
    return Hash32(sha256(block_hash + b"\x02").digest())

def prog_list_chunk_gti(chunk_index: Uint) -> U256:
    gti = GTI_LIST_TREE
    height = PROG_LIST_HEIGHT_FIRST
    for chunk_index >= Uint(1) << height:
        chunk_index -= Uint(1) << height
        gti = gti_merge(gti, GTI_PROG_LIST_NEXT_TREE)
        height += PROG_LIST_HEIGHT_STEP
    gti = gti_merge(gti, GTI_PROG_LIST_SUBTREE)
    return gti_merge(gti, gti_vector(chunk_index, height))

def make_empty_vector_roots(length: Uint) -> List[U256]:
    roots = []
    next_root = U256(0)
    for range(length):
        roots.append(next_root)
        next_root = binary_hash(next_root, next_root)
    return roots

EMPTY_VECTOR_ROOTS = make_empty_vector_roots(256)
EMPTY_LOG_INDEX_ROOT = binary_hash(EMPTY_VECTOR_ROOTS[LOG2_EPOCH_HISTORY], U256(0))

def log_index_empty_subtree(index: U256) -> U256:
    if index == GTI_ROOT:
        return EMPTY_LOG_INDEX_ROOT
    side = gti_split_below(index, 1)
    index = gti_split_above(index, 1)
    height = gti_height(index)
    match side:
        case GTI_LEFT: # Epoch history tree
            if height <= LOG2_EPOCH_HISTORY:
                return EMPTY_VECTOR_ROOTS[LOG2_EPOCH_HISTORY - height]
            index = gti_split_above(index, LOG2_EPOCH_HISTORY)
            return epoch_empty_subtree(index)
        case GTI_RIGHT: # Next index counter
            if height != 0:
                raise AssertionError("Invalid log index tree node")
            return U256(0)
        case _:
            raise AssertionError("Invalid log index tree node")

def epoch_empty_subtree(index: U256) -> U256:
    side = gti_split_below(index, 1)
    index = gti_split_above(index, 1)
    height = gti_height(index)
    match side:
        case GTI_LEFT: # Filter maps subtree
            if height <= LOG2_MAP_HEIGHT + LOG2_MAPS_PER_EPOCH:
                return EMPTY_VECTOR_ROOTS[LOG2_MAP_HEIGHT + LOG2_MAPS_PER_EPOCH - height]
            index = gti_split_above(index, LOG2_MAP_HEIGHT + LOG2_MAPS_PER_EPOCH)
            return prog_list_empty_subtree(index)
        case GTI_RIGHT: # Log entries subtree
            if height <= LOG2_MAPS_PER_EPOCH + LOG2_VALUES_PER_MAP:
                return EMPTY_VECTOR_ROOTS[LOG2_MAPS_PER_EPOCH + LOG2_VALUES_PER_MAP - height]
            index = gti_split_above(index, LOG2_MAPS_PER_EPOCH + LOG2_VALUES_PER_MAP)
            return log_entry_empty_subtree(index)
        case _:
            raise AssertionError("Invalid log index tree node")

def prog_list_empty_subtree(index: U256) -> U256:
    side = gti_split_below(index, 1)
    index = gti_split_above(index, 1)
    height = gti_height(index)
    match side:
        case GTI_LEFT: # Progressive list tree
            if height == 0:
                return U256(0)
            return prog_list_tree_empty_subtree(0, index)
        case GTI_RIGHT: # Length counter
            if height != 0:
                raise AssertionError("Invalid log index tree node")
            return U256(0)
        case _:
            raise AssertionError("Invalid log index tree node")

def prog_list_tree_empty_subtree(tree_level: Uint, index: U256) -> U256:
    side = gti_split_below(index, 1)
    index = gti_split_above(index, 1)
    height = gti_height(index)
    match side:
        case GTI_LEFT: # List elements subtree
            max_height = PROG_LIST_HEIGHT_FIRST + PROG_LIST_HEIGHT_STEP * tree_level
            if height <= max_height:
                return EMPTY_VECTOR_ROOTS[max_height - height]
            raise AssertionError("Invalid log index tree node")
        case GTI_RIGHT: # Next tree level
            if height == 0:
                return U256(0)
            return prog_list_tree_empty_subtree(tree_level + 1, index)
        case _:
            raise AssertionError("Invalid log index tree node")

def log_entry_empty_subtree(index: U256) -> U256:
    side = gti_split_below(index, 1)
    index = gti_split_above(index, 1)
    height = gti_height(index)
    match side:
        case GTI_LEFT: # Log data subtree (or empty in case of block/tx delimiter)
            if height == 0:
                return U256(0)
            return log_data_empty_subtree(index)
        case GTI_RIGHT: # Meta field (log/block/tx, always 4 fields)
            if height > 2:
                raise AssertionError("Invalid log index tree node")
            return EMPTY_VECTOR_ROOTS[2 - height]
        case _:
            raise AssertionError("Invalid log index tree node")

def log_data_empty_subtree(index: U256) -> U256:
    height = gti_height(index)
    if height <= 2:
        return EMPTY_VECTOR_ROOTS[2 - height]
    field = gti_split_below(index, 2)
    sub_index = gti_split_above(index, 2)
    match field:
        case GTI_LOG_DATA_ADDRESS:
            raise AssertionError("Invalid log index tree node")
        case GTI_LOG_DATA_TOPICS:
            return log_topics_empty_subtree(index)
        case GTI_LOG_DATA_DATA:
            return prog_list_empty_subtree(sub_index)
        case _:
            raise AssertionError("Invalid log index tree node")

def log_topics_empty_subtree(index: U256) -> U256:
    side = gti_split_below(index, 1)
    index = gti_split_above(index, 1)
    height = gti_height(index)
    match side:
        case GTI_LEFT: # Topics list entries subtree
           if height > 2:
                raise AssertionError("Invalid log index tree node")
            return EMPTY_VECTOR_ROOTS[2 - height]
        case GTI_RIGHT: # Topics list count field
            if height == 0:
                return U256(0)
           raise AssertionError("Invalid log index tree node")
        case _:
            raise AssertionError("Invalid log index tree node")
