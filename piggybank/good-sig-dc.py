from piggybank_drivers import *
from blspy import (PrivateKey, AugSchemeMPL, G2Element)

dc = get_coin("17057455729c3ced2be2d07d762a7d18a7b38e66d4bec16c14a4a1dd0a850162")

to_puz_hash = bytes.fromhex('ca13bc2f475ba97fcaed9419e70c8d9350fbe1684ceb36935ad266a8e49fce03')

dc_spend = CoinSpend(
    dc,
    DUMMY_MOD,
    Program.to([dc.amount, to_puz_hash])
)

# create a signature
sk: PrivateKey = PrivateKey.from_bytes(bytes.fromhex("5437f185b5c21424a7b6296a77f01ae1aa453b4cec3d388dd39b49bd8eb457d8"))
message: bytes = bytes("hello chia", 'utf-8')
sig: G2Element = AugSchemeMPL.sign(sk, message)

spend_bundle = SpendBundle([dc_spend], sig)
print_json(spend_bundle.to_json_dict())

