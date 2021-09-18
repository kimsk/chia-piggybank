import asyncio
from blspy import G2Element
import json

import time

from cdv.util.load_clvm import load_clvm

from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_spend import CoinSpend
from chia.types.spend_bundle import SpendBundle
from chia.util.bech32m import encode_puzzle_hash, decode_puzzle_hash
from chia.util.config import load_config
from chia.util.default_root import DEFAULT_ROOT_PATH
from chia.util.ints import uint16, uint64
from chia.wallet.transaction_record import TransactionRecord

def print_json(dict):
    print(json.dumps(dict, sort_keys=True, indent=4))

PIGGYBANK_CLSP = "piggybank.clsp"
CONTRIBUTION_CLSP = "contribution.clsp"


# config/config.yaml
config = load_config(DEFAULT_ROOT_PATH, "config.yaml")
self_hostname = config["self_hostname"] # localhost
full_node_rpc_port = config["full_node"]["rpc_port"] # 8555
wallet_rpc_port = config["wallet"]["rpc_port"] # 9256

async def get_coin_async(coin_id: str):
    try:
        full_node_client = await FullNodeRpcClient.create(
                self_hostname, uint16(full_node_rpc_port), DEFAULT_ROOT_PATH, config
            )
        coin_record = await full_node_client.get_coin_record_by_name(bytes32.fromhex(coin_id))
        return coin_record.coin
    finally:
        full_node_client.close()
        await full_node_client.await_closed()


def get_coin(coin_id: str):
    return asyncio.run(get_coin_async(coin_id))


async def get_transaction_async(tx_id: bytes32):
    wallet_id = "1"
    try:
        wallet_client = await WalletRpcClient.create(
            self_hostname, uint16(wallet_rpc_port), DEFAULT_ROOT_PATH, config
        )
        tx = await wallet_client.get_transaction(wallet_id, tx_id)
        return tx
    finally:
        wallet_client.close()
        await wallet_client.await_closed()

def get_transaction(tx_id: bytes32):
    return asyncio.run(get_transaction_async(tx_id))

# Send from your default wallet on your machine
# Wallet has to be running, e.g., chia start wallet
async def send_money_async(amount, address, fee=0):
    wallet_id = "1"
    try:
        print(f"sending {amount} to {address}...")
        # create a wallet client
        wallet_client = await WalletRpcClient.create(
                self_hostname, uint16(wallet_rpc_port), DEFAULT_ROOT_PATH, config
            )
        # send standard transaction
        res = await wallet_client.send_transaction(wallet_id, amount, address, fee)
        tx_id = res.name
        print(f"waiting until transaction {tx_id} is confirmed...")
        # wait until transaction is confirmed
        tx: TransactionRecord = await wallet_client.get_transaction(wallet_id, tx_id)
        while (not tx.confirmed):
            await asyncio.sleep(5)
            tx = await wallet_client.get_transaction(wallet_id, tx_id)
            print(".", end='', flush=True)

        # get coin infos including coin id of the addition with the same puzzle hash
        print(f"\ntx {tx_id} is confirmed.")
        puzzle_hash = decode_puzzle_hash(address)
        coin = next((c for c in tx.additions if c.puzzle_hash == puzzle_hash), None)
        print(f"coin {coin}")
        return coin
    finally:
        wallet_client.close()
        await wallet_client.await_closed()

def send_money(amount, address, fee=0):
    return asyncio.run(send_money_async(amount, address, fee))

def deploy_smart_coin(clsp_file: str, amount: uint64):
    s = time.perf_counter()
    # load coins (compiled and serialized, same content as clsp.hex)
    mod = load_clvm(clsp_file, package_or_requirement=__name__)
    # cdv clsp treehash
    treehash = mod.get_tree_hash()
    # cdv encode
    address = encode_puzzle_hash(treehash, "txch")
    coin = send_money(amount, address)
    elapsed = time.perf_counter() - s
    print(f"deploy {clsp_file} with {amount} mojos to {treehash} in {elapsed:0.2f} seconds.")
    print(f"coin_id: {coin.get_hash().hex()}")

    return coin

# opc '(amount new_amount piggybank_puzhash)'
def solution_for_piggybank(pb_coin: Coin, contrib_amount: uint64) -> Program:
    # print(f"opc '({pb_coin.amount} {pb_coin.amount + contrib_amount} {pb_coin.puzzle_hash})'")
    return Program.to([pb_coin.amount, (pb_coin.amount + contrib_amount), pb_coin.puzzle_hash])

# opc '()'
def solution_for_contribution() -> Program:
    return Program.to([])

async def push_tx_async(spend_bundle: SpendBundle):
    try:
        # create a full node client
        full_node_client = await FullNodeRpcClient.create(
                self_hostname, uint16(full_node_rpc_port), DEFAULT_ROOT_PATH, config
            )
        status = await full_node_client.push_tx(spend_bundle)
        return status
    finally:
        full_node_client.close()
        await full_node_client.await_closed()

def push_tx(spend_bundle: SpendBundle):
    return asyncio.run(push_tx_async(spend_bundle))

def deposit(piggybank_coin: Coin, contribution_coin: Coin):
    # coin information, puzzle_reveal, and solution
    piggybank_spend = CoinSpend(
        piggybank_coin,
        load_clvm(PIGGYBANK_CLSP, package_or_requirement=__name__),
        solution_for_piggybank(piggybank_coin, contribution_coin.amount)
    )

    contribution_spend = CoinSpend(
        contribution_coin,
        load_clvm(CONTRIBUTION_CLSP, package_or_requirement=__name__),
        solution_for_contribution()
    )

    # empty signature i.e., c00000.....
    signature = G2Element()

    # SpendBundle
    spend_bundle = SpendBundle(
            # coin spends
            [
                piggybank_spend,
                contribution_spend
            ],
            # aggregated_signature
            signature,
        )
    print_json(spend_bundle.to_json_dict())
    status = push_tx(spend_bundle)
    print_json(status)

