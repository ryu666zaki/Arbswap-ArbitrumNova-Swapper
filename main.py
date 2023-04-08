import random
from web3 import Web3
import json
import time


# Enter how many times to swap => ETH -> USDC -> ETH = 1 time
TIMES = 10

# Delay between swaps in seconds
sleep_time_min = 2
sleep_time_max = 3

with open("privatekeys.txt", "r") as f:
    private_keys = [line.strip() for line in f.readlines()]

nova_rpc = 'https://nova.arbitrum.io/rpc'
w3 = Web3(Web3.HTTPProvider(nova_rpc))
nova_scan = 'https://nova.arbiscan.io/tx'
chain_id = 42170

arbswap_router_address = Web3.to_checksum_address('0xEe01c0CD76354C383B8c7B4e65EA88D00B06f36f')
router_abi = json.load(open('abi.json', 'r'))
arbswap_router = w3.eth.contract(address=arbswap_router_address, abi=router_abi)


WETH = Web3.to_checksum_address('0x722e8bdd2ce80a4422e880164f2079488e115365')
USDC = Web3.to_checksum_address('0x750ba8b76187092B0D1E87E28daaf484d1b5273b')

def approve(key):
    account = w3.eth.account.from_key(key)
    address = account.address
    nonce = w3.eth.get_transaction_count(address)

    try:
        max_amount = w3.to_wei(2 ** 64 - 1, 'ether')
        max_amount_hex = w3.to_hex(max_amount)[2:].zfill(64)
        transaction = {
            "from": address,
            "to": USDC,
            "data": f"0x095ea7b3{arbswap_router_address[2:].zfill(64)}{max_amount_hex}",
            "gasPrice": w3.eth.gas_price,
            "nonce": nonce,
        }
        gas_estimate = w3.eth.estimate_gas(transaction)
        transaction["gas"] = gas_estimate
        approve_txn = w3.eth.account.sign_transaction(transaction, key)
        tx_hash = w3.eth.send_raw_transaction(approve_txn.rawTransaction)

        print(f'\n>>> USDC Approved | {nova_scan}/{w3.to_hex(tx_hash)}')
    except Exception as error:
        print(f'\n>>> {error}')


def swap(key):
    account = w3.eth.account.from_key(key)
    address = account.address

    eth_balance = w3.eth.get_balance(address)
    nonce = w3.eth.get_transaction_count(address)
    max_for_swap_eth = int(eth_balance - (eth_balance / 5))
    min_for_swap_eth = int(max_for_swap_eth / 2)

    # ETH -> WETH -> USDC
    try:
        swap_amount = random.randint(min_for_swap_eth, max_for_swap_eth)
        deadline = w3.eth.get_block("latest")["timestamp"] + 300
        path = [WETH, USDC]
        amount_out_min = 0
        txn = arbswap_router.functions.swapExactETHForTokens(
            amount_out_min, path, address, deadline
        ).build_transaction({
            "from": address,
            "value": swap_amount,
            "gasPrice": w3.eth.gas_price,
            "nonce": nonce,
        })
        signed_txn = w3.eth.account.sign_transaction(txn, key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        print("{:.3f}".format(w3.from_wei(swap_amount, "ether")))
        print(f'\n>>> {nova_scan}/{w3.to_hex(tx_hash)}')

        time.sleep(4)
    except Exception as error:
        print(f'\n>>> {error}')

    nonce += 1

    # USDC -> WETH -> ETH
    try:
        deadline = w3.eth.get_block("latest")["timestamp"] + 300
        path = [USDC, WETH]
        amount_out_min = 0
        usdc_balance = w3.eth.call({"to": USDC, "data": f"0x70a08231{address[2:].zfill(64)}"}, 'latest')
        usdc_balance = int(usdc_balance.hex(), 16)
        max_for_swap_usdc = int(usdc_balance - (usdc_balance / 5))
        min_for_swap_usdc = int(max_for_swap_usdc / 2)
        swap_amount = random.randint(min_for_swap_usdc, max_for_swap_usdc)

        txn = arbswap_router.functions.swapExactTokensForETH(
            swap_amount, amount_out_min, path, address, deadline
        ).build_transaction({
            "from": address,
            "gasPrice": w3.eth.gas_price,
            "nonce": nonce,
        })
        signed_txn = w3.eth.account.sign_transaction(txn, key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

        print("{:.3f}".format(w3.from_wei(swap_amount, "ether")))

        print(f'\n>>> {nova_scan}/{w3.to_hex(tx_hash)}')
        time.sleep(4)
    except Exception as error:
        print(f'\n>>> {error}')


def main():
    min_time_sleep = sleep_time_min
    max_time_sleep = sleep_time_max
    wait_time = random.randint(min_time_sleep, max_time_sleep)

    for key in private_keys:
        approve(key)
    for key in private_keys:
        count = 0
        while count < TIMES:
            swap(key)
            count += 1
        time.sleep(wait_time)


if __name__ == "__main__":
    main()
