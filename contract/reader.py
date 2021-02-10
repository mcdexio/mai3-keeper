from web3 import Web3

from lib.address import Address
from lib.contract import Contract
from lib.wad import Wad

class MarginAccount():
    def __init__(self, cash: int, position: int, available_cash: int, margin: int, settleable_margin: int, is_initial_margin_safe: bool, is_maintenance_margin_safe: bool, is_margin_safe: bool):
        self.cash = Wad(cash)
        self.position = Wad(position)
        self.available_cash = Wad(available_cash)
        self.margin = Wad(margin)
        self.settleable_margin = Wad(settleable_margin)
        self.is_initial_margin_safe = is_initial_margin_safe
        self.is_maintenance_margin_safe = is_maintenance_margin_safe
        self.is_margin_safe = is_margin_safe


class Reader(Contract):
    abi = Contract._load_abi(__name__, '../abis/Reader.abi')

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self.contract = self._get_contract(web3, self.abi, address)

    def getMarginAccount(self, pool_address, perpetual_index, address) -> MarginAccount:
        margin_account = self.contract.functions.getAccountStorage(pool_address, perpetual_index, address).call()
        return MarginAccount(margin_account[1][0], margin_account[1][1], margin_account[1][2], margin_account[1][3], margin_account[1][4], margin_account[1][5], margin_account[1][6], margin_account[1][7])
