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
        self.web3 = Web3(HTTPProvider(endpoint_uri=config.ETH_RPC_URL, request_kwargs={'headers':{"Origin":"mcdex.io"}}))
        # self.web3 = Web3(HTTPProvider(endpoint_uri=config.ETH_RPC_URL))
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.gas_price = self.web3.toWei(config.GAS_PRICE, "gwei")

        self.perpetuals = {}
        self.reader = Reader(web3=self.web3, address=Address(config.READER_ADDRESS))

        # watcher
        self.watcher = Watcher(self.web3)

    def _set_liquidity_pools(self):
        if config.IS_USE_WHITELIST:
            perpetuals = json.loads(config.PERPETUAL_LIST)
            for perpetual in perpetuals:
                pool_addr = perpetual.split("-")[0]
                pool = LiquidityPool(web3=self.web3, address=Address(pool_addr))
                self.perpetuals[perpetual] = pool
        else:
            self._get_perpetuals()

    def _get_perpetuals(self):
        try:
            query = '''
            {
                perpetuals(where: {position_not: "0", state_in: [%d,%d]}) {
                    id
                }
            }
            ''' % (Status.NORMAL, Status.EMERGENCY)
            res = requests.post(config.FUND_GRAPH_URL, json={'query': query}, timeout=10)
            if res.status_code == 200:
                perpetuals = res.json()['data']['perpetuals']
                self.perpetuals = []
                for perpetual in perpetuals:
                    pool_addr = perpetual.split("-")[0]
                    pool = LiquidityPool(web3=self.web3, address=Address(pool_addr))
                    self.perpetuals[perpetual] = pool
        except Exception as e:
            self.logger.warning(f"get all perpetuals from graph error: {e}")

 
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

    def _check_all_perpetuals(self):
        def thread_fun(perp_key):
            self._check_perpetual_accounts(perp_key)

        # not use pool whitelist, get all pools onchain
        if not config.IS_USE_WHITELIST:
            self._get_perpetuals()

        thread_list = []
        for key in self.perpetuals.keys():
            thread = threading.Thread(target=thread_fun, args=(key,))
            thread_list.append(thread)

        for i in range(len(thread_list)):
            thread_list[i].start()

        for i in range(len(thread_list)):
            thread_list[i].join()

        self.logger.info(f"check all perpetuals end!")


    def _check_perpetual_accounts(self, key):
        perp_index = int(key.split("-")[1])
        pool = self.perpetuals[key]
        try:
            accounts_count = pool.accounts_count(perp_index)
            if accounts_count == 0:
                return
        except Exception as e:
            self.logger.warning(f"get perpetual account count err:{e}")
            return
        self.logger.info(f"accounts_count:{accounts_count} pool:{pool.address} perp_index:{perp_index}")
        accounts = self.reader.getAccountsInfo(pool.address.address, perp_index, 0, accounts_count)
        for account in accounts:
            self.logger.info(f"check_account pool_address:{pool.address} perp_index:{perp_index} address:{account.address} margin:{account.margin} position:{account.position}")
            if not account.is_safe:
                self.logger.info(f"account unsafe:{account}")
                try:
                    tx_hash = pool.liquidateByAMM(perp_index, account.address, self.keeper_account, self.gas_price)
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
            self.watcher.add_block_syncer(self._check_all_perpetuals)
            self.watcher.run()
