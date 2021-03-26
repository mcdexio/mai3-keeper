import os

# eth node rpc request
ETH_RPC_URL = os.environ.get('ETH_RPC_URL', 'https://kovan.infura.io/v3/2bdd050c8d2d40f69e612d9ad2c99119')

# timeout for get transaction receipt(second)
TX_TIMEOUT = os.environ.get('TX_TIMEOUT', 300)
KEEPER_KEY = os.environ.get('KEEPER_KEY', './key_file')

# gas price
GAS_PRICE = os.environ.get('GAS_PRICE', 1)

# contract address
IS_USE_WHITELIST = os.environ.get('IS_USE_WHITELIST', False)
POOL_ADDRESS = os.environ.get('POOL_ADDRESS', '["0xFE62314f9FB010BEBF52808cD5A4c571a47c4c46", "0x1Ef9Db1C1EAF2240DA2a78e581d53b9e833295BE"]')
READER_ADDRESS = os.environ.get('READER_ADDRESS', '0x50DD9E7d582F13637137F8bDD8357E0b6b5f6B5B')
POOL_CREATOR_ADDRESS = os.environ.get('POOL_CREATOR_ADDRESS', '0xF55cF7BbaF548115DCea6DF10c57DF7c7eD88b9b')

IS_TAKE_OVER = os.environ.get('IS_TAKE_OVER', False)

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
