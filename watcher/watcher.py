import logging
import signal
import threading
import time

from web3 import Web3

class Watcher:
    logger = logging.getLogger()

    def __init__(self, web3: Web3 = None):
        self.web3 = web3
        self.block_syncers = []

        self.terminated = False
        self._last_block_time = None

    def run(self):
        if self.web3 is None:
            self.logger.fatal("Init web3 and set for watcher")
            return
        self.logger.info(f"Keeper connected to {self.web3.provider}")
        if self.web3.eth.defaultAccount:
            self.logger.info(f"Keeper operating as {self.web3.eth.defaultAccount}")

        #self._wait_for_node_sync()
        self._start_watching_blocks()
        self.logger.info("Keeper shut down")

    def _wait_for_node_sync(self):
        if 'TestRPC' in self.web3.clientVersion:
            self.logger.info("test node, skip sync")
            return

        if self.web3.net.peerCount == 0:
            self.logger.info(f"Waiting for the node to have at least one peer...")
            while self.web3.net.peerCount == 0:
                time.sleep(0.25)

        if self.web3.eth.syncing:
            self.logger.info(f"Waiting for the node to sync...")
            while self.web3.eth.syncing:
                time.sleep(0.25)

    def add_block_syncer(self, callback):
        assert(callable(callback))
        assert(self.web3 is not None)
        self.block_syncers.append(AsyncThread(callback))

    def set_terminated(self):
        self.terminated = True

    def _start_watching_blocks(self):
        signal.signal(signal.SIGINT, self._sigal_handler)
        signal.signal(signal.SIGTERM, self._sigal_handler)

        self.logger.info("Watching for new blocks")
        event_filter = self.web3.eth.filter('latest')
        while True:
            if self.terminated:
                break

            #if self._last_block_time and (int(time.time()) - self._last_block_time) > 300:
            #    if not self.web3.eth.syncing:
            #        self.logger.fatal("No new blocks received for 300 seconds, the keeper will terminate")
            #        break
            
#            for event in event_filter.get_new_entries():
            self._sync_block()
            time.sleep(100)

        for block_syncer in self.block_syncers:
            block_syncer.wait()


    def _sync_block(self):
        self._last_block_time = int(time.time())
        #block = self.web3.eth.getBlock(block_hash)
        #block_number = block['number']
        #if self.web3.eth.syncing:
        #    self.logger.info(f"the node is syncing, new block #{block_number} ({block_hash}) ignored ")
        #    return 
        
        #max_block_number = self.web3.eth.blockNumber
        #if block_number != max_block_number:
        #    self.logger.debug(f"Ignoring block #{block_number} ({block_hash}),"
        #                            f" as there is already block #{max_block_number} available")
        #    return

        if self.terminated:
            self.logger.debug(f"Ignoring block #{block_number} as keeper is already terminating")

        def on_start():
            self.logger.debug(f"Processing the syncer")

        def on_finish():
            self.logger.debug(f"Finished processing the syncer")
        for block_syncer in self.block_syncers:
            if not block_syncer.run(on_start, on_finish):
                self.logger.debug(f"Ignoring"
                                    f" as previous callback is still running")
                

    def _sigal_handler(self, sig, frame):
        if self.terminated:
            self.logger.warning("Keeper termination already in progress")
        else:
            self.logger.warning("Keeper received SIGINT/SIGTERM signal, will terminate gracefully")
            self.terminated = True

class AsyncThread:
    def __init__(self, callback):
        self.callback = callback
        self.thread = None

    def run(self, on_start=None, on_finish=None) -> bool:
        #ensure the same block_syncer only one thread running at the same time
        if self.thread is None or not self.thread.is_alive():
            def thread_target():
                if on_start is not None:
                    on_start()
                self.callback()
                if on_finish is not None:
                    on_finish()

            self.thread = threading.Thread(target=thread_target)
            self.thread.start()
            return True
        else:
            return False

    def wait(self):
        if self.thread is not None:
            self.thread.join()
