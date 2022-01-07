import asyncio

from blspy import (PrivateKey, AugSchemeMPL, G2Element)
from cdv.test import Network, Wallet
from cdv.util.load_clvm import load_clvm
from chia.consensus.default_constants import DEFAULT_CONSTANTS
from chia.types.blockchain_format.program import Program
from chia.types.coin_spend import CoinSpend
from chia.types.condition_opcodes import ConditionOpcode
from chia.types.spend_bundle import SpendBundle
from chia.util.hash import std_hash

network: Network = asyncio.run(Network.create())
asyncio.run(network.farm_block())
alice: Wallet = network.make_wallet("alice")
asyncio.run(network.farm_block(farmer=alice))
print(f'alice balance:\t{alice.balance()}')

bob: Wallet = network.make_wallet("bob")

MOD = load_clvm("simple_pay_to_delegated.clsp", package_or_requirement=__name__, search_paths=["../include"])

# create a smart coin and curry in alice's pk
amt = 1_000_000
alice_mod = MOD.curry(alice.pk())
alice_coin = asyncio.run(
    alice.launch_smart_coin(
        alice_mod,
        amt=amt
    )
)

print(f'alice smart coin:\t{alice_coin}')

# (delegated_puzzle solution)
solution = Program.to([
    1, # (mod conditions conditions)
    [
        [ConditionOpcode.CREATE_COIN, bob.puzzle_hash, amt],
        [ConditionOpcode.ASSERT_MY_AMOUNT, alice_coin.amount]
    ]
])

# create a spend bundle with alice's signature
spend = CoinSpend(
    alice_coin.as_coin(),
    alice_mod,
    solution 
)

# message: bytes = std_hash(bytes("hello delegated puzzle", "utf-8"))
message: bytes = Program.to(1).get_tree_hash() # (mod conditions conditions)
alice_sk: PrivateKey = alice.pk_to_sk(alice.pk())
sig: G2Element = AugSchemeMPL.sign(
    alice_sk,
    message
    + alice_coin.name()
    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA,
)

spend_bundle = SpendBundle([spend], sig)

print(f'\npush spend bundle:\n{spend_bundle}\n')
asyncio.run(network.push_tx(spend_bundle))
print(f'alice balance:\t{alice.balance()}')
print(f'bob balance:\t{bob.balance()}')

alice_coin_id = alice_coin.name()
alice_coin_record = asyncio.run(
    network.sim_client.get_coin_record_by_name(alice_coin_id))
print(alice_coin_record)

coin_spend: CoinSpend = asyncio.run(
    network.sim_client.get_puzzle_and_solution(alice_coin_id, alice_coin_record.spent_block_index))
print(coin_spend.puzzle_reveal)

asyncio.run(network.close())

import json

def print_json(dict):
    print(json.dumps(dict, sort_keys=True, indent=4))

print_json(spend_bundle.to_json_dict(include_legacy_keys = False, exclude_modern_keys = False))
