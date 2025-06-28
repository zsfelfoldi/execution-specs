"""
A `Block` is a single link in the chain that is Ethereum. Each `Block` contains
a `Header` and zero or more transactions. Each `Header` contains associated
metadata like the block number, parent block hash, and how much gas was
consumed by its transactions.

Together, these blocks form a cryptographically secure journal recording the
history of all state transitions that have happened since the genesis of the
chain.
"""
from dataclasses import dataclass
from typing import Tuple

from ethereum_types.bytes import Bytes, Bytes8, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint

from ..crypto.hash import Hash32
from .fork_types import Address, Bloom, Root

LOG_MAP_HEIGHT = Uint(16)
LOG_MAP_WIDTH = Uint(24)
LOG_MAPS_PER_EPOCH = Uint(10)
LOG_VALUES_PER_MAP = Uint(16)
LOG_EPOCH_HISTORY = Uint(24)
= Uint()
= Uint()
= Uint()
= Uint()
= Uint()
= Uint()
= Uint()
= Uint()
= Uint()
= Uint()
= Uint()
= Uint()

	baseRowGroupLength:  32,
	baseRowLengthRatio:  8,
	logLayerDiff:        4,
	logEpochHistory:     24,
	progListHeightFirst: 0,
	progListHeightStep:  2,
}

type Params struct {
	logMapHeight        uint // log2(mapHeight)
	logMapWidth         uint // log2(mapWidth)
	logMapsPerEpoch     uint // log2(mapsPerEpoch)
	logValuesPerMap     uint // log2(logValuesPerMap)
	baseRowLengthRatio  uint // baseRowLength / average row length
	logLayerDiff        uint // maxRowLength log2 growth per layer
	logEpochHistory     uint
	progListHeightFirst uint
	progListHeightStep  uint
	// derived fields
	mapHeight     uint32 // filter map height (number of rows)
	mapsPerEpoch  uint32 // number of maps in an epoch
	baseRowLength uint32 // maximum number of log values per row on layer 0
	valuesPerMap  uint64 // number of log values marked on each filter map
	// not affecting consensus
	baseRowGroupLength uint32 // length of base row groups in local database
}



@dataclass
class LogIndexState:
    """
    Withdrawals represent a transfer of ETH from the consensus layer (beacon
    chain) to the execution layer, as validated by the consensus layer. Each
    withdrawal is listed in the block's list of withdrawals. See [`block`]

    [`block`]: ref:ethereum.prague.blocks.Block.withdrawals
    """

    next_index: U64
    current_map: List[FilterRow]


