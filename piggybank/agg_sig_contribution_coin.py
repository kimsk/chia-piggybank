from piggybank_drivers import *
from blspy import (PrivateKey, AugSchemeMPL, G2Element)
from chia.consensus.default_constants import DEFAULT_CONSTANTS

## contribution coins
cc = get_coin("063dc19d4cff257354ab0ee936e2c6935f0a4208c6690ada4f7e5ae9fbf74e38")
cc_solution = Program.to([cc.amount])
cc_spend = CoinSpend(
    cc,
    CONTRIBUTION_MOD,
    cc_solution
)

## piggybank coin
pc = get_coin("a39ffe19087aa846a6cb5c970a92f32366b32b7cfa2772f39005cd11b2e11a7b")
pc_solution = Program.to([pc.amount, [cc.amount], pc.puzzle_hash])
pc_spend = CoinSpend(
    pc,
    PIGGYBANK_MOD,
    pc_solution
)

coin_spends = [
    pc_spend,
    cc_spend
]

# create a signature
sk: PrivateKey = PrivateKey.from_bytes(bytes.fromhex("5437f185b5c21424a7b6296a77f01ae1aa453b4cec3d388dd39b49bd8eb457d8"))
message: bytes = std_hash(int_to_bytes(cc.amount))

sig: G2Element = AugSchemeMPL.sign(sk,
                    message
                    + cc.name()
                    # mainnet's GENESIS_CHALLENGE
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
                )

spend_bundle = SpendBundle(coin_spends, sig)
print_json(spend_bundle.to_json_dict(include_legacy_keys = False, exclude_modern_keys = False))
