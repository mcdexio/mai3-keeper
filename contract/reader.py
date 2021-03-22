from web3 import Web3

from lib.address import Address
from lib.contract import Contract
from lib.wad import Wad

class MarginAccount():
    def __init__(self, address, available_cash: int, position: int, margin: int, is_safe: bool):
        self.address = Address(address)
        self.position = Wad(position)
        self.available_cash = Wad(available_cash)
        self.margin = Wad(margin)
        self.is_safe = is_safe


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

    def getAccountsInfo(self, pool_address, perpetual_index, begin, end) -> []:
        accountsInfo = self.contract.functions.getAccountsInfo(pool_address, perpetual_index, begin, end).call()
        res = []
        for account in accountsInfo[1]:
            res.append(MarginAccount(account[0], account[1], account[2], account[3], account[4]))
        return res
