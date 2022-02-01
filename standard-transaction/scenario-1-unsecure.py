from blspy import (PrivateKey, AugSchemeMPL, G1Element, G2Element)
from clvm_tools.binutils import disassemble
from chia.consensus.default_constants import DEFAULT_CONSTANTS
from chia.types.blockchain_format.program import Program
from chia.types.coin_spend import CoinSpend
from chia.types.condition_opcodes import ConditionOpcode
from chia.types.spend_bundle import SpendBundle
from chia.wallet.puzzles.p2_delegated_puzzle_or_hidden_puzzle import (
    DEFAULT_HIDDEN_PUZZLE_HASH, 
    calculate_synthetic_public_key, 
    calculate_synthetic_secret_key, 
    puzzle_for_public_key_and_hidden_puzzle_hash,
    calculate_synthetic_offset
)


from sim import alice, bob, charlie, get_coin_by_puzzle_hash, farm, get_coin, get_normal_coin_spend, push_tx, end
import utils

farm(alice)
farm(alice)
farm(bob)

# alice and bob wants to save XCH together for charlie
print(f'alice balance: {alice.balance()}')
print(f'bob balance: {bob.balance()}')
print(f'charlie balance: {charlie.balance()}')

# UNSECURE
# 1. alice_sk + DEFAULT_HIDDEN_PUZZLE_HASH -> alice_syn_sk
# 2. bob_sk + DEFAULT_HIDDEN_PUZZLE_HASH -> bob_syn_sk
# 3. alice_syn_sk + bob_syn_sk -> syn_sk
# 4. syn_sk -> agg_pk
# 5. agg_pk + DEFAULT_HIDDEN_PUZZLE_HASH -> saving puzzle
# 6. syn_sk + DEFAULT_HIDDEN_PUZZLE_HASH -> saving_syn_sk
# 7. sig = AugSchemeMPL.sign(saving_synthetic_sk, msg)
# keybase://chat/chia_network.public#dev/20795
# alice and bob separately create synthetic_sk from thier sk (never shared!)
alice_synthetic_sk = calculate_synthetic_secret_key(
        alice.sk_,
        DEFAULT_HIDDEN_PUZZLE_HASH
    )


bob_synthetic_sk = calculate_synthetic_secret_key(
        bob.sk_,
        DEFAULT_HIDDEN_PUZZLE_HASH
    )

# aggregate to create synthetic_sk
synthetic_sk = PrivateKey.aggregate([alice_synthetic_sk, bob_synthetic_sk])
agg_pk = synthetic_sk.get_g1()
synthetic_pk = calculate_synthetic_public_key(agg_pk, DEFAULT_HIDDEN_PUZZLE_HASH)

print(f'synthetic_sk: {synthetic_sk}')
print(f'agg_pk: {agg_pk}')
print(f'synthetic_pk: {synthetic_pk}')

# alice & bob saving
saving_puzzle = puzzle_for_public_key_and_hidden_puzzle_hash(agg_pk, DEFAULT_HIDDEN_PUZZLE_HASH)
saving_puzzle_hash = saving_puzzle.get_tree_hash()


xch = 1_000_000_000_000
alice_coin = get_coin(alice, xch)
alice_spend, alice_sig_msg, alice_sig, alice_synthetic_pk = get_normal_coin_spend(
    alice, alice_coin,
    [
        # alice creates coin
        [ConditionOpcode.CREATE_COIN, saving_puzzle_hash, xch * 2],
        [ConditionOpcode.CREATE_COIN, alice.puzzle_hash, alice_coin.amount - xch],
    ])

bob_coin = get_coin(bob, xch)
bob_spend, bob_sig_msg, bob_sig, bob_synthetic_pk = get_normal_coin_spend(
    bob, bob_coin,
    [
        [ConditionOpcode.CREATE_COIN, bob.puzzle_hash, bob_coin.amount - xch],
    ])

print(calculate_synthetic_public_key(alice.pk(), DEFAULT_HIDDEN_PUZZLE_HASH))
print(disassemble(puzzle_for_public_key_and_hidden_puzzle_hash(alice.pk(), DEFAULT_HIDDEN_PUZZLE_HASH)))
print(disassemble(alice.puzzle))
print(disassemble(saving_puzzle))
print(saving_puzzle_hash)

agg_sig = AugSchemeMPL.aggregate([
            alice_sig, 
            bob_sig
        ])

spend_bundle = SpendBundle(
    [
        alice_spend,
        bob_spend
    ],
    agg_sig
)

assert AugSchemeMPL.aggregate_verify(
    [
        alice_synthetic_pk,
        bob_synthetic_pk
    ], 
    [
        alice_sig_msg,
        bob_sig_msg
    ], agg_sig)

# saving coin created
result = push_tx(spend_bundle)
saving_coin = get_coin_by_puzzle_hash(saving_puzzle_hash)[0].coin
print(f'saving_coin: {saving_coin}')
print(f'alice balance: {alice.balance()}')
print(f'bob balance: {bob.balance()}')
print(f'charlie balance: {charlie.balance()}')

# both now wants to send to charlie

conditions =  [
    [ConditionOpcode.CREATE_COIN, charlie.puzzle_hash, saving_coin.amount]
]
delegated_puzzle_solution = Program.to((1, conditions))
coin_spend = CoinSpend(
        saving_coin,
        saving_puzzle,
        Program.to([[], delegated_puzzle_solution, []])
    )

print(coin_spend)

msg = (
        delegated_puzzle_solution.get_tree_hash()
        + saving_coin.name()
        + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
)

# calculate saving_synthetic_sk to sign the spend bundle
saving_synthetic_sk = calculate_synthetic_secret_key(
        synthetic_sk,
        DEFAULT_HIDDEN_PUZZLE_HASH
    )
sig = AugSchemeMPL.sign(saving_synthetic_sk, msg)
print(sig)
assert AugSchemeMPL.aggregate_verify(
    [
        synthetic_pk
    ],
    [
        msg
    ], 
    sig)

spend_bundle = SpendBundle([coin_spend], sig)
result = push_tx(spend_bundle)
print(result)
print(f'final charlie balance: {charlie.balance()}')

end()
utils.print_json(spend_bundle.to_json_dict(include_legacy_keys = False, exclude_modern_keys = False))
