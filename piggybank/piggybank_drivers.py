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
from chia.util.clvm import int_to_bytes
from chia.util.config import load_config
from chia.util.default_root import DEFAULT_ROOT_PATH
from chia.util.hash import std_hash
from chia.util.ints import uint16, uint64
from chia.wallet.transaction_record import TransactionRecord

def print_json(dict):
    print(json.dumps(dict, sort_keys=True, indent=4))

# c23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8 | original
# 5c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64 | w/ CREATE_PUZZLE_ANNOUNCEMENT
# 2e2546cae60daa0ddfd948bf1d3b783c6fad278e4b5c96b2ad60119807ef2ea7 | w/ ASSERT_MY_PUZZLEHASH
# d02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d | w/ CREATE_PUZZLE_ANNOUNCEMENT for contribution coins
PIGGYBANK_MOD = load_clvm("piggybank.clsp", package_or_requirement=__name__, search_paths=["../include"])

# 4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a | original
# e6b571b019744c25e599c0f63593c4003b025c8f437c695b422b13d09bec9107 | w/ ASSERT_PUZZLE_ANNOUNCEMENT
# 8b198e66bc96c121341ca38b995af1dcd7e56b10d13fc5b809d38fd7274b2155 | w/ new piggybank puzzle hash with ASSERT_MY_PUZZLEHASH
# 6aae6f4638981ba070d1f4b7ba5fa091ccec531369165ffe222aa868816a695d | w/ ASSERT_PUZZLE_ANNOUNCEMENT my_amount
CONTRIBUTION_MOD = load_clvm("contribution.clsp", package_or_requirement=__name__, search_paths=["../include"])

# b92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd
DUMMY_MOD = load_clvm("dummy_coin.clsp", package_or_requirement=__name__, search_paths=["../include"])

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

def get_coin_by_coin_information(parent_coin_info: str, puzzle_hash: str, amount: uint64):
    coin_id = std_hash(bytes32.fromhex(parent_coin_info) + bytes32.fromhex(puzzle_hash) + int_to_bytes(amount))
    return get_coin(coin_id.hex())

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

def deploy_smart_coin(mod: Program, amount: uint64):
    s = time.perf_counter()
    # cdv clsp treehash
    treehash = mod.get_tree_hash()
    # cdv encode
    address = encode_puzzle_hash(treehash, "txch")
    coin = send_money(amount, address)
    elapsed = time.perf_counter() - s
    print(f"deploy smart coin with {amount} mojos to {treehash} in {elapsed:0.2f} seconds.")
    print(f"coin_id: {coin.get_hash().hex()}")

    return coin

# opc '(amount new_amount piggybank_puzhash)'
def solution_for_piggybank(pb_coin: Coin, contrib_amount: uint64) -> Program:
    # print(f"opc '({pb_coin.amount} {pb_coin.amount + contrib_amount} {pb_coin.puzzle_hash})'")
    return Program.to([pb_coin.amount, (pb_coin.amount + contrib_amount), pb_coin.puzzle_hash])

# opc '()'
def solution_for_contribution() -> Program:
    return Program.to([])

# opc '(new_amount puzzle_hash)'
def solution_for_dummy(dummy_coin: Coin, contrib_amount: uint64, puzzle_hash: str) -> Program:
    return Program.to([(dummy_coin.amount + contrib_amount), bytes32.fromhex(puzzle_hash)])

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

def get_piggybank_coin_spend(piggybank_coin: Coin, contribution_amount):
    # coin information, puzzle_reveal, and solution
    return CoinSpend(
        piggybank_coin,
        PIGGYBANK_MOD,
        solution_for_piggybank(piggybank_coin, contribution_amount)
    )

def get_dummy_coin_spend(dummy_coin: Coin, contribution_amount, puzzle_hash):
    # coin information, puzzle_reveal, and solution
    return CoinSpend(
        dummy_coin,
        DUMMY_MOD,
        solution_for_dummy(dummy_coin, contribution_amount, puzzle_hash)
    )

def deposit_piggybank(piggybank_coin: Coin, contribution_coins):
    if type(contribution_coins) != list:
        contribution_coins: list = [contribution_coins]

    contribution_amount = sum([c.amount for c in contribution_coins])
    piggybank_coin_spend = get_piggybank_coin_spend(piggybank_coin, contribution_amount)
    cc_puzzle = CONTRIBUTION_MOD
    cc_solution = solution_for_contribution()
    contribution_spends = [CoinSpend(c, cc_puzzle, cc_solution) for c in contribution_coins]

    # empty signature i.e., c00000.....
    signature = G2Element()

    coin_spends = [cs for cs in contribution_spends]
    coin_spends.append(piggybank_coin_spend)
    spend(coin_spends, signature)

def deposit_dummy(dummy_coin: Coin, contribution_coins, puzzle_hash):
    if type(contribution_coins) != list:
        contribution_coins: list = [contribution_coins]

    contribution_amount = sum([c.amount for c in contribution_coins])
    dummy_coin_spend = get_dummy_coin_spend(dummy_coin, contribution_amount, puzzle_hash)
    cc_puzzle = CONTRIBUTION_MOD
    cc_solution = solution_for_contribution()
    contribution_spends = [CoinSpend(c, cc_puzzle, cc_solution) for c in contribution_coins]

    # empty signature i.e., c00000.....
    signature = G2Element()

    coin_spends = [cs for cs in contribution_spends]
    coin_spends.append(dummy_coin_spend)
    spend(coin_spends, signature)

def deposit_to_puzzle_hash(pc: Coin, cc: Coin, puzzle_hash: bytes32):
    piggybank_spend = CoinSpend(
        pc,
        PIGGYBANK_MOD,
        Program.to([pc.amount, (pc.amount + cc.amount), puzzle_hash])

    )
    contribution_spend = CoinSpend(cc, CONTRIBUTION_MOD, solution_for_contribution())

    spend(
        [piggybank_spend, contribution_spend],
        signature = G2Element()
    )

def deposit_contrbution(contribution_coins):
    if type(contribution_coins) != list:
        contribution_coins: list = [contribution_coins]

    cc_puzzle = CONTRIBUTION_MOD
    cc_solution = solution_for_contribution()
    contribution_spends = [CoinSpend(c, cc_puzzle, cc_solution) for c in contribution_coins]

    # empty signature i.e., c00000.....
    signature = G2Element()

    coin_spends = [cs for cs in contribution_spends]
    spend(coin_spends, signature)

def spend(coin_spends: list, signature):
    # SpendBundle
    spend_bundle = SpendBundle(
            # coin spends
            coin_spends,
            # aggregated_signature
            signature,
        )
    print_json(spend_bundle.to_json_dict())
    status = push_tx(spend_bundle)
    print_json(status)

