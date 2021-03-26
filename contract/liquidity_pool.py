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

# class MarginAccount():
#     def __init__(self, cash: int, position: int, available_cash: int, margin: int, settleable_margin: int, is_initial_margin_safe: bool, is_maintenance_margin_safe: bool, is_margin_safe: bool):
#         self.cash = Wad(cash)
#         self.position = Wad(position)
#         self.available_cash = Wad(available_cash)
#         self.margin = Wad(margin)
#         self.settleable_margin = Wad(settleable_margin)
#         self.is_initial_margin_safe = is_initial_margin_safe
#         self.is_maintenance_margin_safe = is_maintenance_margin_safe
#         self.is_margin_safe = is_margin_safe

class Liquidate:
    def __init__(self, price: int, amount: int):
        assert(isinstance(price, int))
        assert(isinstance(amount, int))

        self.price = Wad(price)
        self.amount = Wad(amount)

class LiquidityPool(Contract):
    abi = Contract._load_abi(__name__, '../abis/LiquidityPool.abi')
    logger = logging.getLogger()

    def __init__(self, web3: Web3, address: Address):
        assert(isinstance(web3, Web3))
        assert(isinstance(address, Address))

        self.web3 = web3
        self.address = address
        self.contract = self._get_contract(web3, self.abi, address)

    def getPerpetualCount(self):
        pool_info = self.contract.functions.getLiquidityPoolInfo().call()
        return pool_info[6]

    def accounts_count(self, perpetual_index) -> int:
        return self.contract.functions.getActiveAccountCount(perpetual_index).call()

    def perpetual_status(self, perpetual_index) -> Status:
        perp_info = self.contract.functions.getPerpetualInfo(perpetual_index).call()
        return Status(perp_info[0])

    def accounts(self, perpetual_index, begin: int, end: int):
        accounts = self.contract.functions.listActiveAccounts(perpetual_index, begin, end).call()
        return accounts

    # def getMarginAccount(self, perpetual_index, address) -> MarginAccount:
    #     margin_account = self.contract.functions.getMarginAccount(perpetual_index, address).call()
    #     return MarginAccount(margin_account[0], margin_account[1], margin_account[2], margin_account[3], margin_account[4], margin_account[5], margin_account[6], margin_account[7])


    def liquidateByAMM(self, perpetual_index, trader, user, gas_price):
        gas = self.contract.functions.liquidateByAMM(perpetual_index, trader).estimateGas({
                    'from': user.address,
                    'gasPrice': gas_price
                })

        tx_hash = self.contract.functions.liquidateByAMM(perpetual_index, trader).transact({
                    'from': user.address,
                    'gasPrice': gas_price
                })
        return tx_hash

    def liquidateByTrader(self, perpetual_index, trader, amount, price, deadline, user, gas_price):
        tx_hash = self.contract.functions.liquidateByTrader(perpetual_index, trader, amount.value, price.value, deadline).transact({
                    'from': user.address,
                    'gasPrice': gas_price
                })
        return tx_hash



