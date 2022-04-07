import asyncio
from logging import raiseExceptions
from warnings import catch_warnings
from web3 import Web3, middleware
from requests import get
import json
from dotenv import load_dotenv
import os
from brownie import accounts, config
import random
from web3.middleware import geth_poa_middleware
from web3.gas_strategies.time_based import fast_gas_price_strategy


API_KEY = "WHNW7X7PNWY539JGQWI95JWYS7ARGX3UEX"

w3 = Web3(Web3.HTTPProvider('https://kovan.infura.io/v3/80cd20a6eaac4e7aa4249e7aaff12c9d'))

print(w3.isConnected())
load_dotenv()

bot_address = "0x7d3a625977bfd7445466439e60c495bdc2855367"
abi = json.loads('[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[],"name":"Ping","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes32","name":"txHash","type":"bytes32"}],"name":"Pong","type":"event"},{"inputs":[],"name":"ping","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"pinger","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes32","name":"_txHash","type":"bytes32"}],"name":"pong","outputs":[],"stateMutability":"nonpayable","type":"function"}]')
address=Web3.toChecksumAddress(bot_address)

contract = w3.eth.contract(address=address, abi=abi)

PRIVATE_KEY = os.getenv('PRIVATE_KEY')

def get_account():
    return accounts.add(config["wallets"]["from_key"])

my_address = Web3.toChecksumAddress("0xe8909ce1C1EF8b480548385F3CB7A442d41CC88D")

w3.middleware_onion.inject(geth_poa_middleware, layer=0)
w3.middleware_onion.add(middleware.time_based_cache_middleware)
w3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
w3.middleware_onion.add(middleware.simple_cache_middleware)


def handle_event(event):
    print(Web3.toJSON(event))
    string_event = Web3.toJSON(event)
    json_data = json.loads(string_event)
    print(json_data['transactionHash'])
    tx_hash = json_data['transactionHash']
    #w3.eth.defaultAccount = get_account()
    chain_id = w3.eth.chain_id
    nonce = w3.eth.get_transaction_count(my_address)
    print(f"This is the nonce right now: {nonce}")
    random_nonce = random.randint(50, 500)
    w3.eth.set_gas_price_strategy(fast_gas_price_strategy)
    tx_pong = contract.functions.pong(tx_hash).buildTransaction({
        'chainId': chain_id,
        #'from': w3.eth.defaultAccount,
        # give +1 to nonce if needed, or change back gas to 25000
        # It worked like this ! - EXCEPT WITH gas set to 25000!!
        # Now set back the gas to 25000 to use less! (from 70000)
        'nonce': nonce,
        'gas': 70000,
        'gasPrice': w3.eth.gas_price,
        })
        
    signed_tx = w3.eth.account.sign_transaction(tx_pong, private_key = PRIVATE_KEY)

    tx_pong_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    #tx_receipt = w3.eth.get_transaction_receipt(tx_pong_hash)
    print(f"Tx Pong successful! {tx_pong_hash}")

    #ValueError: {'code': -32010, 'message': 'Transaction gas price supplied is too low. There is another transaction with same nonce in the queue. Try increasing the gas price or incrementing the nonce.'}

async def log_loop(event_filter, poll_interval):
    while True:
        for Ping in event_filter.get_new_entries():
            handle_event(Ping)

        await asyncio.sleep(poll_interval)

def main():
    event_filter = contract.events.Ping.createFilter(fromBlock='latest')
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(
            asyncio.gather(
                log_loop(event_filter, 2))),
    finally:
        loop.close()



if __name__ == "__main__":
    main()


