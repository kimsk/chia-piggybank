import asyncio
import utils

from blspy import (PrivateKey, AugSchemeMPL, G2Element)
from cdv.test import Network, SmartCoinWrapper, Wallet
from cdv.util.load_clvm import load_clvm
from chia.consensus.default_constants import DEFAULT_CONSTANTS
from chia.types.blockchain_format.program import Program
from chia.types.coin_spend import CoinSpend
from chia.types.condition_opcodes import ConditionOpcode
from chia.types.spend_bundle import SpendBundle
from chia.util.hash import std_hash
from chia.wallet.puzzles.p2_delegated_puzzle_or_hidden_puzzle import DEFAULT_HIDDEN_PUZZLE_HASH, calculate_synthetic_secret_key, puzzle_for_public_key_and_hidden_puzzle_hash

network: Network = asyncio.run(Network.create())
asyncio.run(network.farm_block())

alice: Wallet = network.make_wallet("alice")
bob: Wallet = network.make_wallet("bob")
carol: Wallet = network.make_wallet("carol")

asyncio.run(network.farm_block(farmer=alice))
print(f'alice balance:\t{alice.balance()}')
amt = 1_000_000
alice_coin = asyncio.run(alice.choose_coin(amt))
assert alice_coin != None
print(f'alice coin:\t{alice_coin}')

# alice want to send coin to carol, but bob has to approve the amount of the spend as well
condition_args = [
    [ConditionOpcode.AGG_SIG_ME, bob.pk(), std_hash(bytes(amt))],
    [ConditionOpcode.CREATE_COIN, carol.puzzle_hash, amt],
]

delegated_puzzle_solution = Program.to((1, condition_args))
synthetic_sk: PrivateKey = calculate_synthetic_secret_key(
    alice.sk_,
    DEFAULT_HIDDEN_PUZZLE_HASH
)
solution = Program.to([[], delegated_puzzle_solution, []])

alice_puzzle = puzzle_for_public_key_and_hidden_puzzle_hash(
    alice.pk(), DEFAULT_HIDDEN_PUZZLE_HASH
)

alice_sig = AugSchemeMPL.sign(synthetic_sk,
    (
        delegated_puzzle_solution.get_tree_hash()
        + alice_coin.name()
        + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
    )
)

spend_bundle = SpendBundle(
    [
        CoinSpend(
            alice_coin.as_coin(),
            alice.puzzle,
            solution,
        )
    ],
    alice_sig,
)

# spend bundle with alice's signature only won't work
result = asyncio.run(network.push_tx(spend_bundle))
assert result['error'] == 'Err.BAD_AGGREGATE_SIGNATURE'

# later the spend bundle and synthetic pk is sent to bob
# bob verifies the delegated_puzzle_solution hash
assert AugSchemeMPL.verify(synthetic_sk.get_g1(),
    delegated_puzzle_solution.get_tree_hash()
    + alice_coin.name()
    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA,
    alice_sig
)

# bob signs and aggregate the signature
bob_sig = AugSchemeMPL.sign(bob.sk_,
    (   std_hash(bytes(amt))
        + alice_coin.name()
        + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
    )
)

agg_sig = AugSchemeMPL.aggregate([alice_sig, bob_sig])
print(f"alice sig:\t{alice_sig}")
print(f"bob sig:\t{bob_sig}")
print(f"agg sig:\t{agg_sig}")

# bob replace alice_sig with the agg_sig
spend_bundle = SpendBundle(
    [
        CoinSpend(
            alice_coin.as_coin(),
            alice.puzzle,
            solution,
        )
    ],
    agg_sig,
)

# spend bundle with alice's signature only won't work
result = asyncio.run(network.push_tx(spend_bundle))
print(f'alice balance:\t{alice.balance()}')
print(f'carol balance:\t{carol.balance()}')

asyncio.run(network.close())
