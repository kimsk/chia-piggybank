from piggybank_drivers import *
from blspy import (PrivateKey, AugSchemeMPL, G2Element)

dc = get_coin("5c6e36370def3d8bd306cf22b45e830cc9e0b960aa4aa90e86992e17824dec9b")

to_puz_hash = bytes.fromhex('ca13bc2f475ba97fcaed9419e70c8d9350fbe1684ceb36935ad266a8e49fce03')

dc_spend = CoinSpend(
    dc,
    DUMMY_MOD,
    Program.to([dc.amount, to_puz_hash])
)

# create a signature
sk: PrivateKey = PrivateKey.from_bytes(bytes.fromhex("5437f185b5c21424a7b6296a77f01ae1aa453b4cec3d388dd39b49bd8eb457d8"))
message: bytes = std_hash(int_to_bytes(dc.amount) + to_puz_hash)
sig: G2Element = AugSchemeMPL.sign(sk, message)

# let's change dc_spend solution
# dc_spend = CoinSpend(
#     dc,
#     DUMMY_MOD,
#     Program.to([dc.amount - 50, to_puz_hash])
# )
spend_bundle = SpendBundle([dc_spend], sig)
print_json(spend_bundle.to_json_dict(include_legacy_keys = False, exclude_modern_keys = False))
