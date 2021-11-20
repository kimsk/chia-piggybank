from piggybank_drivers import *
from blspy import (PrivateKey, AugSchemeMPL, G2Element)
from chia.consensus.default_constants import DEFAULT_CONSTANTS

#dc = get_coin("81887c5a720bd3686bba40c0403803a5d55cc9301d7bd7fe6e26603b6a6b44d6")
#dc = get_coin("c33e96eacf048aa9f8f020c28811b6eb4ee75438d1a8b46983653bcf759a93f1")
dc = get_coin("3f1158d762e4378041871177d42537f021947f6a56fad6fb9591814ca666eca8")

to_puz_hash = bytes.fromhex('ca13bc2f475ba97fcaed9419e70c8d9350fbe1684ceb36935ad266a8e49fce03')

dc_spend = CoinSpend(
    dc,
    DUMMY_MOD,
    Program.to([dc.amount, to_puz_hash])
)

# create a signature
sk: PrivateKey = PrivateKey.from_bytes(bytes.fromhex("5437f185b5c21424a7b6296a77f01ae1aa453b4cec3d388dd39b49bd8eb457d8"))
message: bytes = std_hash(int_to_bytes(dc.amount) + to_puz_hash)

# for AGG_SIG_ME, we need to concat dummy coin id and the GENESIS_CHALLENGE
# Or you can use DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA for mainnet
# https://github.com/Chia-Network/chia-blockchain/blob/main/chia/consensus/default_constants.py#L33
# 
sig: G2Element = AugSchemeMPL.sign(sk,
                    message
                    + dc.name()
                    # mainnet's GENESIS_CHALLENGE
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
                )

spend_bundle = SpendBundle([dc_spend], sig)
print_json(spend_bundle.to_json_dict(include_legacy_keys = False, exclude_modern_keys = False))
