# A Liquidate Bot for MCDEX Perpetual

The MCDEX Perpetual contract incentives external agents, called keepers, to monitor and keep margin accounts safe.

This bot keeps track of margin accounts in the MCDEX perpetual contract and finds out accounts that have been unsafe. The bot will initiate a "liquidateByAMM" command to the Ethereum network:
* You will earn keeper reward
* The perpetual's AMM will earn penalty prize
* The perpetual's AMM will get the liquidated position

## Getting Started
### install
```
# we need python 3.6
git clone https://github.com/mcdexio/mai3-keeper.git
cd mai3-keeper
pip install -r requirements.txt
```
1. Editing `config.example/config.py`, then "mv config.example config":
  * Set rpc.url to an ETH node. We recommend that you start an Ethereum node yourself (ex: geth or parity). You can also register an infura account and paste the node url from infura dashboard.
  * Set keeper account private_key. you may need [export the private key from MetaMask](https://metamask.zendesk.com/hc/en-us/articles/360015289632-How-to-Export-an-Account-Private-Key)
2. Run it `python main.py`

