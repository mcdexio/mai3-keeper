import os

# eth node rpc request
ETH_RPC_URL = os.environ.get('ETH_RPC_URL', 'https://kovan.infura.io/v3/f7fc9890cc8e44dcaeb2e51ce9927b83')

# timeout for get transaction receipt(second)
TX_TIMEOUT = os.environ.get('TX_TIMEOUT', 300)
KEEPER_KEY = os.environ.get('KEEPER_KEY', './key_file')

# gas price
GAS_PRICE = os.environ.get('GAS_PRICE', 1)

# contract address
POOL_ADDRESS = os.environ.get('POOL_ADDRESS', '["0x043f3FB76d0bafF2F24B1E894210177fF51B98cC", "0x0323D333A8aAb656D79Ba1adDBC8e32D9f30c498"]')

IS_TAKE_OVER = os.environ.get('IS_TAKE_OVER', True)

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
