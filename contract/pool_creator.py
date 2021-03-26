from web3 import Web3
import logging

from lib.address import Address
from lib.contract import Contract
from lib.wad import Wad
from enum import Enum

class Status(Enum):
     INVALID = 0
     INITIALIZING = 1
     NORMAL = 2
     EMERGENCY = 3
     CLEARED = 4

class PoolCreator(Contract):
    abi = Contract._load_abi(__name__, '../abis/PoolCreator.abi')
    logger = logging.getLogger()

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self.contract = self._get_contract(web3, self.abi, address)

    def getLiquidityPoolCount(self):
        pool_count = self.contract.functions.getLiquidityPoolCount().call()
        return pool_count

    def listLiquidityPools(self, begin: int, end: int):
        pools = self.contract.functions.listLiquidityPools(begin, end).call()
        return pools

