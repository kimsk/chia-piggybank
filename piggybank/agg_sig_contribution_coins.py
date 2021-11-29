from piggybank_drivers import *
from blspy import (PrivateKey, AugSchemeMPL, G2Element)
from chia.consensus.default_constants import DEFAULT_CONSTANTS

## contribution coins
cc = get_coin("0fdf33a1ab85ed0b442d1c2f78c3ffa450ec33036c6da97511e0bf3d268f6749")
cc_solution = Program.to([cc.amount])
cc_spend = CoinSpend(
    cc,
    CONTRIBUTION_MOD,
    cc_solution
)

cc2 = get_coin("ba86adfbbcab04c06109e5dc2702106bac456666dda24c31b0ac10598132467e")
cc_solution2 = Program.to([cc2.amount])
cc_spend2 = CoinSpend(
    cc2,
    CONTRIBUTION_MOD,
    cc_solution2
)

## piggybank coin
pc = get_coin("760f612304a5eb627081632a3c94ef7d4a1aeeaf31e2a29047a6aacb40c0da7b")
pc_solution = Program.to([pc.amount, [cc.amount, cc2.amount], pc.puzzle_hash])
pc_spend = CoinSpend(
    pc,
    PIGGYBANK_MOD,
    pc_solution
)

coin_spends = [
    pc_spend,
    cc_spend, cc_spend2
]

# create a signature
sk: PrivateKey = PrivateKey.from_bytes(bytes.fromhex("5437f185b5c21424a7b6296a77f01ae1aa453b4cec3d388dd39b49bd8eb457d8"))
sig1: G2Element = AugSchemeMPL.sign(sk,
                    std_hash(int_to_bytes(cc.amount))
                    + cc.name()
                    # mainnet's GENESIS_CHALLENGE
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
                )

sig2: G2Element = AugSchemeMPL.sign(sk,
                    std_hash(int_to_bytes(cc2.amount))
                    + cc2.name()
                    # mainnet's GENESIS_CHALLENGE
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
                )

sig = AugSchemeMPL.aggregate([sig1, sig2])
assert(AugSchemeMPL.verify(sk.get_g1(), 
                    std_hash(int_to_bytes(cc.amount))
                    + cc.name()
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA,
                    sig1))

spend_bundle = SpendBundle(coin_spends, sig)
print_json(spend_bundle.to_json_dict(include_legacy_keys = False, exclude_modern_keys = False))
