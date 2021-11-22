from piggybank_drivers import *
from blspy import (PrivateKey, AugSchemeMPL, G2Element)
from chia.consensus.default_constants import DEFAULT_CONSTANTS

## contribution coins
# 100000000
cc = get_coin("032380717266e352532856bc3cdb37cdb0e086b9e7eb3121e774f213dafd40a1")
cc_solution = Program.to([cc.amount])
cc_spend = CoinSpend(
    cc,
    CONTRIBUTION_MOD,
    cc_solution
)
# 300000000
cc2 = get_coin("b2b6063600b339ca233f62bd3b0766ef00b4b28d784f0f61f020fbfc1d621c37")
cc_solution2 = Program.to([cc2.amount])
cc_spend2 = CoinSpend(
    cc2,
    CONTRIBUTION_MOD,
    cc_solution2
)

# 100000000
cc3 = get_coin("f364b35f232bb057a08e7c7afc353cbb274456fa8b2cbf9579c1e6d96f8c9894")
cc_solution3 = Program.to([cc3.amount])
cc_spend3 = CoinSpend(
    cc3,
    CONTRIBUTION_MOD,
    cc_solution3
)

## piggybank coin
## only cc and cc2 are contributed, cc3 would be spent as fees
pc = get_coin("9a1c86f46a4bac9069372eecb25dbce63642c2aee9d6497c95244db3dbc5800f")
pc_solution = Program.to([pc.amount, [cc.amount, cc2.amount], pc.puzzle_hash])
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
                    # mainnet's GENESIS_CHALLENGE
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
                )

sig2: G2Element = AugSchemeMPL.sign(sk,
                    std_hash(int_to_bytes(cc2.amount))
                    + cc2.name()
                    # mainnet's GENESIS_CHALLENGE
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
                )

sig3: G2Element = AugSchemeMPL.sign(sk,
                    std_hash(int_to_bytes(cc3.amount))
                    + cc3.name()
                    # mainnet's GENESIS_CHALLENGE
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
                )

sig = AugSchemeMPL.aggregate([sig1, sig2, sig3])

spend_bundle = SpendBundle(coin_spends, sig)
print_json(spend_bundle.to_json_dict(include_legacy_keys = False, exclude_modern_keys = False))
