from piggybank_drivers import *
from blspy import (PrivateKey, AugSchemeMPL, G2Element)
from chia.consensus.default_constants import DEFAULT_CONSTANTS

## contribution coins
# 100000000
cc = get_coin("ab800c725ee21f1afc180793270df17e8b2b6c98395d29b534cc22d476a18ceb")
cc_solution = Program.to([cc.name(), cc.amount])
cc_spend = CoinSpend(
    cc,
    CONTRIBUTION_MOD,
    cc_solution
)
# 300000000
cc2 = get_coin("46564cec8e013310b4deee4d357c873a8d642bc807dafac165d3c2045fe06680")
cc_solution2 = Program.to([cc2.name(), cc2.amount])
cc_spend2 = CoinSpend(
    cc2,
    CONTRIBUTION_MOD,
    cc_solution2
)

# 100000000
cc3 = get_coin("94115a9ec073588f67c997c785609077256fe1ce9e3ecbdabfe8576e50bcbaa3")
cc_solution3 = Program.to([cc3.name(), cc3.amount])
cc_spend3 = CoinSpend(
    cc3,
    CONTRIBUTION_MOD,
    cc_solution3
)

## piggybank coin
## only cc and cc2 are contributed, cc3 would be spent as fees
pc = get_coin("74122f64aea8c9addd228d6d8096bb7353fb895dc77e9794d6ee71529211d169")
pc_solution = Program.to(
    [pc.amount, 
    [
        [cc.name(), cc.amount],
        [cc2.name(), cc2.amount], 
        [cc3.name(), cc3.amount]
    ],
    pc.puzzle_hash]
)
pc_spend = CoinSpend(
    pc,
    PIGGYBANK_MOD,
    pc_solution
)

coin_spends = [
    pc_spend,
    cc_spend, cc_spend2, cc_spend3
]

# create a signature
sk: PrivateKey = PrivateKey.from_bytes(bytes.fromhex("5437f185b5c21424a7b6296a77f01ae1aa453b4cec3d388dd39b49bd8eb457d8"))
sig1: G2Element = AugSchemeMPL.sign(sk,
                    std_hash(int_to_bytes(cc.amount))
                    + cc.name()
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
                )

sig2: G2Element = AugSchemeMPL.sign(sk,
                    std_hash(int_to_bytes(cc2.amount))
                    + cc2.name()
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
                )

sig3: G2Element = AugSchemeMPL.sign(sk,
                    std_hash(int_to_bytes(cc3.amount))
                    + cc3.name()
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
                )

sig = AugSchemeMPL.aggregate([sig1, sig2, sig3])

spend_bundle = SpendBundle(coin_spends, sig)
print_json(spend_bundle.to_json_dict(include_legacy_keys = False, exclude_modern_keys = False))
