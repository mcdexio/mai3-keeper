import os

# eth node rpc request
ETH_RPC_URL = os.environ.get('ETH_RPC_URL', 'https://kovan5.arbitrum.io/rpc')

# timeout for get transaction receipt(second)
TX_TIMEOUT = os.environ.get('TX_TIMEOUT', 300)
KEEPER_KEY_LIST = os.environ.get('KEEPER_KEY_LIST', '[./key_file]')

# gas price
GAS_PRICE = os.environ.get('GAS_PRICE', 1)

# contract address
MAX_NUM = int(os.environ.get('MAX_NUM', 100))
IS_USE_WHITELIST = os.environ.get('IS_USE_WHITELIST', False)
PERPETUAL_LIST = os.environ.get('PERPETUAL_LIST', '{"0xab324146c49b23658e5b3930e641bdbdf089cbac-0":"0x1cf22b7f84f86c36cb191bb24993eda2b191399e", "0xab324146c49b23658e5b3930e641bdbdf089cbac-1":"0x6ee936bdbd329063e8ce1d13f42efef912e85221"}')

# notice lowercase
POOL_BLACK_LIST = os.environ.get('POOL_BLACK_LIST', '["0xfe62314f9fb010bebf52808cd5a4c571a47c4c46"]')
READER_ADDRESS = os.environ.get('READER_ADDRESS', '0x50DD9E7d582F13637137F8bDD8357E0b6b5f6B5B')
IS_TAKE_OVER = os.environ.get('IS_TAKE_OVER', False)

# mcdex perpetual graph
GRAPH_URL = os.environ.get('GRAPH_URL', 'https://api.thegraph.com/subgraphs/name/mcdexio/mcdex3-kovan1')
PRICE_URL = os.environ.get('PRICE_URL', 'https://mcdex.io/simple-oracle')

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "simple": {
            "format": "%(asctime)s %(levelname)-7s - %(message)s - [%(filename)s:%(lineno)d:%(funcName)s]",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
        "file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": "./log/keeper.log",
            "maxBytes": 104857600, # 100MB
            "backupCount": 7,
            "encoding": "utf8"
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    }
}
