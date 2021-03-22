import logging
import logging.config
import time
import json
import requests
import threading
import math

from web3 import Web3, HTTPProvider, middleware
import eth_utils
from eth_utils import encode_hex
from eth_account import Account
from web3.middleware import construct_sign_and_send_raw_middleware, geth_poa_middleware

import config
from lib.address import Address
from lib.wad import Wad
from watcher import Watcher
from contract.liquidity_pool import LiquidityPool, Status
from contract.reader import Reader, MarginAccount

class Keeper:
    logger = logging.getLogger()

    def __init__(self, args: list, **kwargs):
        logging.config.dictConfig(config.LOG_CONFIG)
        self.keeper_account = None
        #self.web3 = Web3(HTTPProvider(endpoint_uri=config.ETH_RPC_URL, request_kwargs={'headers':{"Origin":"mcdex.io"}}))
        self.web3 = Web3(HTTPProvider(endpoint_uri=config.ETH_RPC_URL))
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.gas_price = self.web3.toWei(config.GAS_PRICE, "gwei")

        self.pools = []
        self.reader = Reader(web3=self.web3, address=Address(config.READER_ADDRESS))
        # watcher
        self.watcher = Watcher(self.web3)

    def _set_liquidity_pools(self):
        pools_address = json.loads(config.POOL_ADDRESS)
        for addr in pools_address:
            pool = LiquidityPool(web3=self.web3, address=Address(addr))
            self.pools.append(pool)
 
    def _check_keeper_account(self):
        with open(config.KEEPER_KEY) as f:
            read_key = f.read().replace("\n","")
            try:
                account = Account()
                acct = account.from_key(read_key)
                print(acct.address)
                self.keeper_account = Address(acct.address)
                self.web3.middleware_onion.add(construct_sign_and_send_raw_middleware(acct))
            except Exception as e:
                self.logger.warning(f"check private key error: {e}")
                return False
            
        return True

    def _check_all_pools(self):
        def thread_fun(pool_idx):
            self._check_pool_accounts(pool_idx)

        thread_list = []
        for pool_idx in range(len(self.pools)):
            thread = threading.Thread(target=thread_fun, args=(pool_idx,))
            thread_list.append(thread)

        for i in range(len(thread_list)):
            thread_list[i].start()

        for i in range(len(thread_list)):
            thread_list[i].join()

        self.logger.info(f"check all pools end!")


    def _check_pool_accounts(self, pool_idx):
        pool = self.pools[pool_idx]
        perp_count = pool.getPerpetualCount()
        for perp_index in range(perp_count):
            # check perpetual status
            perp_status = pool.perpetual_status(perp_index)
            if perp_status != Status.NORMAL and perp_status != Status.EMERGENCY:
                self.logger.info(f"perpetual contract status is {perp_status}. continue")
                continue
            accounts_count = pool.accounts_count(perp_index)
            if accounts_count == 0:
                continue
            self.logger.info(f"accounts_count:{accounts_count} pool:{pool.address} perp_index:{perp_index}")
            #accounts = pool.accounts(perp_index, 0, accounts_count)
            accounts = self.reader.getAccountsInfo(pool.address.address, perp_index, 0, accounts_count)
            for account in accounts:
                #margin_account = self.reader.getMarginAccount(pool.address.address, perp_index, account)
                #self.logger.info(f"check_account address:{account} margin:{margin_account.margin} position:{margin_account.position} cash:{margin_account.cash} available_cash:{margin_account.available_cash}")
                #if not margin_account.is_maintenance_margin_safe:
                self.logger.info(f"check_account address:{account.address} margin:{account.margin} position:{account.position} available_cash:{account.available_cash}")
                if not account.is_safe:
                    self.logger.info(f"account unsafe:{account}")
                    try:
                        tx_hash = pool.liquidateByAMM(perp_index, account, self.keeper_account, self.gas_price)
                        transaction_status = self._wait_transaction_receipt(tx_hash, 10)
                        if transaction_status:
                            self.logger.info(f"liquidate success. address:{account}")
                        else:
                            self.logger.info(f"liquidate fail. address:{account}")
                    except Exception as e:
                        self.logger.fatal(f"liquidate failed. address:{account} error:{e}")

    def _wait_transaction_receipt(self, tx_hash, times):
        self.logger.info(f"tx_hash:{self.web3.toHex(tx_hash)}")
        for i in range(times):
            try:
                tx_receipt = self.web3.eth.waitForTransactionReceipt(tx_hash, config.TX_TIMEOUT)
                self.logger.info(tx_receipt)
                status = tx_receipt['status']

                if status == 0:
                    # transaction failed
                    return False
                elif status == 1:
                    # transaction success
                    return True
            except:
                continue


    def main(self):
        if self._check_keeper_account():
            self._set_liquidity_pools()
            self.watcher.add_block_syncer(self._check_all_pools)
            self.watcher.run()
