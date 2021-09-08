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
from contract.liquidity_pool import LiquidityPool
from contract.reader import Reader, MarginAccount

class KeeperAccount():
    def __init__(self, address: Address):
        self.address = address
        self.is_used = False
        self.lock = threading.Lock()

class Perpetual():
    def __init__(self, pool: LiquidityPool, oracle: str):
        self.pool = pool
        self.status = None
        self.oracle = oracle
        self.margin_accounts = []

    def save_margin_accounts(self, margin_accounts):
        self.margin_accounts = margin_accounts

    def set_status(self, status):
        self.status = status

class Keeper:
    logger = logging.getLogger()

    def __init__(self, args: list, **kwargs):
        logging.config.dictConfig(config.LOG_CONFIG)
        self.keeper_accounts = []
        # self.web3 = Web3(HTTPProvider(endpoint_uri=config.ETH_RPC_URL, request_kwargs={'headers':{"Origin":"mcdex.io"}}))
        self.web3 = Web3(HTTPProvider(endpoint_uri=config.ETH_RPC_URL))
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.gas_price = self.web3.toWei(config.GAS_PRICE, "gwei")

        self.perpetuals = {}
        self.oracles = {}
        self.reader = Reader(web3=self.web3, address=Address(config.READER_ADDRESS))

        # watcher
        self.watcher = Watcher(self.web3)

    def _set_liquidity_pools(self):
        if config.IS_USE_WHITELIST:
            perpetuals = json.loads(config.PERPETUAL_LIST)
            for perpetual, oracle in perpetuals.items():
                pool_addr = perpetual.split("-")[0]
                pool = LiquidityPool(web3=self.web3, address=Address(pool_addr))
                perp = Perpetual(pool, oracle.lower())
                self.perpetuals[perpetual] = perp
                self.oracles[oracle.lower()] = 0
        else:
            self._get_perpetuals()

    def _get_perpetuals(self):
        try:
            query = '''
            {
                perpetuals(where: {openInterest_not: "0", state:2}) {
                    id
                    oracleAddress
                }
            }
            '''
            res = requests.post(config.GRAPH_URL, json={'query': query}, timeout=5)
            if res.status_code == 200:
                perpetuals = res.json()['data']['perpetuals']
                self.perpetuals = {}
                for perpetual in perpetuals:
                    pool_addr = perpetual['id'].split("-")[0]
                    if pool_addr in config.POOL_BLACK_LIST:
                        self.logger.info(f"pool in black list: {pool_addr}")
                        continue
                    pool = LiquidityPool(web3=self.web3, address=Address(pool_addr))
                    perp = Perpetual(pool, perpetual['oracleAddress'])
                    self.oracles[perpetual['oracleAddress']] = 0
                    self.perpetuals[perpetual['id']] = perp
        except Exception as e:
            self.logger.warning(f"get all perpetuals from graph error: {e}")

    def _get_oracle_price(self, oracle):
        try:
            res = requests.get(f'{config.PRICE_URL}/expected_{oracle}.json', timeout=5)
            if res.status_code == 200:
                price = float(res.json()['price'])
                return price
        except Exception as e:
            self.logger.warning(f"get oracle {oracle} price error: {e}")
        return 0

 
    def _check_keeper_account(self):
        key_list = json.loads(config.KEEPER_KEY_LIST)
        for key in key_list:
            with open(key) as f:
                read_key = f.read().replace("\n","")
                try:
                    account = Account()
                    acct = account.from_key(read_key)
                    self.logger.info(f"keeper address: {acct.address}")
                    self.keeper_accounts.append(Address(acct.address))
                    self.web3.middleware_onion.add(construct_sign_and_send_raw_middleware(acct))
                except Exception as e:
                    self.logger.warning(f"check private key error: {e}")
                    return False
            
        return True

    def _get_all_margin_accounts(self):
        def thread_fun(perp_key):
            self._get_perpetual_accounts(perp_key)

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


    def _get_perpetual_accounts(self, key):
        perp_index = int(key.split("-")[1])
        perpetual = self.perpetuals[key]
        is_continue = True
        i = 0
        margin_accounts = []
        while is_continue:
            try:
                accounts = self.reader.getAccountsInfo(perpetual.pool.address.address, perp_index, i*config.MAX_NUM, (i+1)*config.MAX_NUM)
                if len(accounts) < config.MAX_NUM :
                    is_continue = False
                i += 1
            except Exception as e:
                self.logger.warning(f"getAccountsInfo error:{e}")

            for account in accounts:
                # if account is unsafe, call liquidate 
                if not account.is_safe:
                    self.logger.info(f"check_account pool_address:{perpetual.pool.address} perp_index:{perp_index} address:{account.address} margin:{account.margin} position:{account.position}")
                    self.logger.info(f"account unsafe:{account.address}")
                    self._send_liquidate_transaction(perpetual.pool, perp_index, account)
                # save margin account sort by position
                if len(margin_accounts) > 0 and abs(account.position) > abs(margin_accounts[0].position):
                    margin_accounts.insert(0, account)
                elif account.position != Wad(0):
                    margin_accounts.append(account)

        perpetual.save_margin_accounts(margin_accounts)

    def _check_oracle_prices(self):
        def thread_fun(perp_key):
            self._check_margin_accounts(perp_key)

        thread_list = []
        for oracle in self.oracles.keys():
            price = self._get_oracle_price(oracle)
            # oracle price update
            if price > 0 and price != self.oracles[oracle]:
                for key, perp in self.perpetuals.items():
                    if perp.oracle == oracle:
                        thread = threading.Thread(target=thread_fun, args=(key,))
                        thread_list.append(thread)

        for i in range(len(thread_list)):
            thread_list[i].start()

        for i in range(len(thread_list)):
            thread_list[i].join()

        self.logger.info(f"check all perpetuals end!")
        return

    def _check_margin_accounts(self, key):
        perp_index = int(key.split("-")[1])
        perpetual = self.perpetuals[key]
        for account in perpetual.margin_accounts:
            if not account.is_safe:
                self.logger.info(f"check_account pool_address:{perpetual.pool.address} perp_index:{perp_index} address:{account.address} margin:{account.margin} position:{account.position}")
                self.logger.info(f"account unsafe:{account.address}")
                self._send_liquidate_transaction(perpetual.pool, perp_index, account)

    def _send_liquidate_transaction(self, pool, perp_index, account):
        tx_hash = None
        is_send = False
        while True:
            for keeper in self.keeper_accounts:
                if not keeper.is_used:
                    self.lock.acquire()
                    try:
                        tx_hash = pool.liquidateByAMM(perp_index, account.address, self.keeper_account, self.gas_price)
                    except Exception as e:
                        self.logger.fatal(f"liquidate failed. address:{account.address} error:{e}")
                    finally:
                        is_send = True
                        keeper.is_used = False
                        self.lock.release()
            if is_send:
                break

        if tx_hash is not None:
            self._wait_transaction_receipt_in_thread(tx_hash)

    def _wait_transaction_receipt_in_thread(self, tx_hash):
        # wait receipt in thread
        thread = threading.Thread(target=self._wait_transaction_receipt, args=(tx_hash, 10))
        thread.start()

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
            # pools in whitelist or get pools which openInterest not 0 from subgraph
            self._set_liquidity_pools()
            # thread to get margin account, and sort by position
            self.watcher.add_block_syncer(self._get_all_margin_accounts)
            # thread to check margin account, and call liquidate when account is unsafe
            self.watcher.add_price_syncer(self._check_oracle_prices)
            self.watcher.run()
