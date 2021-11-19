# Aggregated Signature

So far, in all of our spend bundles, we have been using an empty signature, `0xc00000000000000000000000000...`, to simplify our learning. However, this lets any (malicious or not) farmers to be able to modify our `coin_solutions` (especially the `solution`) inside the spend bundles. 

## Creating A Signature

To prevent our spend to be modified by any malicious farmer, we have to sign our spend with our private/secret key. If anything in the spend bundle has been tampered, the signature will be invalid which makes the spend bundle invalid.

Let see some samples of signing and verifying the message via CLI and python:

```sh
# generate a random set of keys
❯ $key = cdv inspect keys --random; $key[0]; $key[1]

Secret Key: 71005b4be2f8a24427dbdcaaae48cab31fa86afc0fe73c40b88b0841f40e4c4d
Public Key: 9688d47b019c2bda4228cae785b2ccd5bf0933b45aa6c355a45323f848f7c1cdd80605ee27f4b8d4b8e379c959f639f3

# sign a message with a private key
❯ cdv inspect signatures --secret-key "71005b4be2f8a24427dbdcaaae48cab31fa86afc0fe73c40b88b0841f40e4c4d" --utf-8 "hello chia"
a63edc8f27e6f78f01317b7c7714be6b3e59e9d237d4e2f63af832efff71dfc87038df5a52201374cd082a6cd73a80f20594e4f11a74a5d90f0ad9d5b6f02b97b7cdce496158c951e250b02afb46b0b3ee5b9a97035f0b629f80399d86e700e8

# verify the message and signature with a public key
❯ chia keys verify --message "hello chia" --public_key "9688d47b019c2bda4228cae785b2ccd5bf0933b45aa6c355a45323f848f7c1cdd80605ee27f4b8d4b8e379c959f639f3" --signature "a63edc8f27e6f78f01317b7c7714be6b3e59e9d237d4e2f63af832efff71dfc87038df5a52201374cd082a6cd73a80f20594e4f11a74a5d90f0ad9d5b6f02b97b7cdce496158c951e250b02afb46b0b3ee5b9a97035f0b629f80399d86e700e8"
True
```
```python
from blspy import (PrivateKey, AugSchemeMPL,
                   G1Element, G2Element)

sk: PrivateKey = PrivateKey.from_bytes(bytes.fromhex("71005b4be2f8a24427dbdcaaae48cab31fa86afc0fe73c40b88b0841f40e4c4d"))
pk: G1Element = sk.get_g1()

message: bytes = bytes("hello chia", 'utf-8')
signature: G2Element = AugSchemeMPL.sign(sk, message)

# Verify the signature
ok: bool = AugSchemeMPL.verify(pk, message, signature)
assert ok
```

Once, it's done, we can send a bundle of signature and the message to other people, and they can verify the authenticity of the message and ensure that the message is coming from us and the message was not modified.

## Aggregated Signature

[In Chia, we use BLS Signatures to sign any relevant data.](https://chialisp.com/docs/coins_spends_and_wallets#bls-aggregated-signatures). BLS allows you to compress the multiple signatures into a single signature called **aggregated signature**. In addition , BLS signature can aggregate public keys into a single key that will verify their aggregated signatures. The obvious benefit or aggregated signature is that it supports multisig without using a lot of space.

Let's see how can we create and verify an aggregated signature:

```sh
# generate three random keys and use them in our python code
❯ cdv inspect keys --random;
Secret Key: 0a900677882bcfa970724a381900e7b6c0d40425fda8a2d1f2db90a13d960472
Public Key: a4d7da9a1c5210352e4487abc45cc09ca7e523630740e208087c4eb5f0c7ea85819c7affae1b1c846feabf49b071ad1d
...

❯ cdv inspect keys --random;
Secret Key: 0f90b1a9ca144b969283a989eb8c5273cbe192df58eb79e551ed538759f9ee14
Public Key: a4a0b8aed35ad944b287d0a46245c0bc66e1b0ae21cfa0190d90f2dc0a16b0482c44ad5f8b7256357d4f108d4ed5a9d1
...

❯ cdv inspect keys --random;
Secret Key: 12acd472632e04bf69ff6bf9715e37fdd8d752874e29ae44ba8d53bb3744b4fc
Public Key: a4d62928c171673d15f268812499870346e7ce2d78321a23fc9584ea3c21f090a84215cc522a15de967a96aaae710587
...
```

```python
from blspy import (PrivateKey, BasicSchemeMPL,
                   G1Element, G2Element)

sk1: PrivateKey = PrivateKey.from_bytes(bytes.fromhex("0a900677882bcfa970724a381900e7b6c0d40425fda8a2d1f2db90a13d960472"))
pk1: G1Element = sk1.get_g1()
assert pk1 == G1Element.from_bytes(bytes.fromhex("a4d7da9a1c5210352e4487abc45cc09ca7e523630740e208087c4eb5f0c7ea85819c7affae1b1c846feabf49b071ad1d"))
sk2: PrivateKey = PrivateKey.from_bytes(bytes.fromhex("0f90b1a9ca144b969283a989eb8c5273cbe192df58eb79e551ed538759f9ee14"))
pk2: G1Element = sk2.get_g1()
assert pk2 == G1Element.from_bytes(bytes.fromhex("a4a0b8aed35ad944b287d0a46245c0bc66e1b0ae21cfa0190d90f2dc0a16b0482c44ad5f8b7256357d4f108d4ed5a9d1"))
sk3: PrivateKey = PrivateKey.from_bytes(bytes.fromhex("12acd472632e04bf69ff6bf9715e37fdd8d752874e29ae44ba8d53bb3744b4fc"))
pk3: G1Element = sk3.get_g1()
assert pk3 == G1Element.from_bytes(bytes.fromhex(" a4d62928c171673d15f268812499870346e7ce2d78321a23fc9584ea3c21f090a84215cc522a15de967a96aaae710587"))

# a message is signed with three different private keys to get three signatures
message = "hello chia"
message_as_bytes = bytes(message, "utf-8")
sig1: G2Element = BasicSchemeMPL.sign(sk1, message_as_bytes)
sig2: G2Element = BasicSchemeMPL.sign(sk2, message_as_bytes)
sig3: G2Element = BasicSchemeMPL.sign(sk3, message_as_bytes)

# verify signatures
verify1 = BasicSchemeMPL.verify(pk1, message_as_bytes, sig1)
verify2 = BasicSchemeMPL.verify(pk2, message_as_bytes, sig2)
verify3 = BasicSchemeMPL.verify(pk3, message_as_bytes, sig3)

# aggregate three signatures to one
agg_sig = BasicSchemeMPL.aggregate([sig1, sig2, sig3])

# aggregate three public keys to one aggregated public key
agg_pk = pk1 + pk2 + pk3
agg_verify = BasicSchemeMPL.verify(agg_pk, message_as_bytes, agg_sig)
```

Now we know how to sign our message using either CLI (i.e., `cdv` and `chia`) or via Python. Next is to use aggregated signature to make sure that our spend bundle won't be modified by anyone.

## AGG_SIG_UNSAFE & AGG_SIG_ME

The way chia can verify the authenticity of the spend bundle is to use conditions, `AGG_SIG_UNSAFE` and `AGG_SIG_ME`. 

### AGG_SIG_UNSAFE

Let's try the `AGG_SIG_UNSAFE` first. The `AGG_SIG_UNSAFE` condition requires `PUBKEY` and `message`. We add a `AGG_SIG_UNSAFE` condition to make sure that the spend is valid only if the aggregated signature contains a signature from signing the **message** by the associated **private key**.  

Let's start with restricting dummy coin to be spendable only by a person with a **secret key** that is associated with the **public key** hard-coded to our dummy coin.

```sh
❯ cdv inspect keys --random
Secret Key: 5437f185b5c21424a7b6296a77f01ae1aa453b4cec3d388dd39b49bd8eb457d8
Public Key: a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1
```

Here is our original dummy coin that anyone can spend.

```lisp
# b92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd
(mod (
        new_amount
        puzzle_hash
     )

    (include condition_codes.clib)

    (list
        (list CREATE_COIN puzzle_hash new_amount)
    )
)
```

Let's add `AGG_SIG_UNSAFE` condition and hard code the public key we get from above:

```lisp
# 32632a65eda0d8964cf7a25c900d1545260c544727c128e99aa9074d7992c05e
(mod (
        new_amount
        puzzle_hash
     )

    (include condition_codes.clib)
    (defconstant PUBKEY 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1)

    (list
        (list CREATE_COIN puzzle_hash new_amount)
        (list AGG_SIG_UNSAFE PUBKEY "hello chia")
    )
)
```

We can then deploy few dummy coins to the blockchain.

```sh
❯ cdv rpc coinrecords --by puzhash 32632a65eda0d8964cf7a25c900d1545260c544727c128e99aa9074d7992c05e -ou -nd
{
    "17057455729c3ced2be2d07d762a7d18a7b38e66d4bec16c14a4a1dd0a850162": {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x371a8ca374cf53410ed06f7c3c90654394b322cff884890eb78588f33c46e464",
            "puzzle_hash": "0x32632a65eda0d8964cf7a25c900d1545260c544727c128e99aa9074d7992c05e"
        },
        "coinbase": false,
        "confirmed_block_index": 890307,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1637292886
    },...
}
```

Next step is to try to create spend bundles for our dummy coins to the following puzzle hash, `ca13bc2f475ba97fcaed9419e70c8d9350fbe1684ceb36935ad266a8e49fce03`.

First we will create a valid spend bundle with a proper signature:

```python
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
```

```json
{
    "aggregated_signature": "0x901ae9cbb7a2b795c3c45a0f8ccdd177abee060294e2523a1af64634c89edb15ed873005070d803a637f3c656faead0811ccb624921b9eb30a75f84f4fcc9043c6582b009d94acb4e01d23be1cc535128c04d51ff806544e57641babee148152",
    "coin_solutions": [
        {
            "coin": {
                "amount": 100,
                "parent_coin_info": "0x371a8ca374cf53410ed06f7c3c90654394b322cff884890eb78588f33c46e464",
                "puzzle_hash": "0x32632a65eda0d8964cf7a25c900d1545260c544727c128e99aa9074d7992c05e"
            },
            "puzzle_reveal": "0xff02ffff01ff04ffff04ff0affff04ff0bffff04ff05ff80808080ffff04ffff04ff04ffff04ff0effff01ff8a68656c6c6f2063686961808080ff808080ffff04ffff01ff31ff33b0a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1ff018080",
            "solution": "0xff64ffa0ca13bc2f475ba97fcaed9419e70c8d9350fbe1684ceb36935ad266a8e49fce0380"
        }
    ]
}
```

Let's check the signature manually and inspect the spend bundle.

```sh
❯ chia keys verify --message "hello chia" --public_key "a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1" --signature "901ae9cbb7a2b795c3c45a0f8ccdd177abee060294e2523a1af64634c89edb15ed873005070d803a637f3c656faead0811ccb624921b9eb30a75f84f4fcc9043c6582b009d94acb4e01d23be1cc535128c04d51ff806544e57641babee148152"

True

❯ cdv inspect spendbundles ./good-sig.json -db -sd
...
[{"aggregated_signature": "0x901ae9cbb7a2b795c3c45a0f8ccdd177abee060294e2523a1af64634c89edb15ed873005070d803a637f3c656faead0811ccb624921b9eb30a75f84f4fcc9043c6582b009d94acb4e01d23be1cc535128c04d51ff806544e57641babee148152", "coin_solutions": [{"coin": {"parent_coin_info": "0x371a8ca374cf53410ed06f7c3c90654394b322cff884890eb78588f33c46e464", "puzzle_hash": "0x32632a65eda0d8964cf7a25c900d1545260c544727c128e99aa9074d7992c05e", "amount": 100}, "puzzle_reveal": "0xff02ffff01ff04ffff04ff0affff04ff0bffff04ff05ff80808080ffff04ffff04ff04ffff04ff0effff01ff8a68656c6c6f2063686961808080ff808080ffff04ffff01ff31ff33b0a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1ff018080", "solution": "0xff64ffa0ca13bc2f475ba97fcaed9419e70c8d9350fbe1684ceb36935ad266a8e49fce0380"}]}]

Debugging Information
---------------------
================================================================================
consuming coin (0x371a8ca374cf53410ed06f7c3c90654394b322cff884890eb78588f33c46e464 0x32632a65eda0d8964cf7a25c900d1545260c544727c128e99aa9074d7992c05e 100)
  with id 17057455729c3ced2be2d07d762a7d18a7b38e66d4bec16c14a4a1dd0a850162


brun -y main.sym '(a (q 4 (c 10 (c 11 (c 5 ()))) (c (c 4 (c 14 (q "hello chia"))) ())) (c (q 49 51 . 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1) 1))' '(100 0xca13bc2f475ba97fcaed9419e70c8d9350fbe1684ceb36935ad266a8e49fce03)'
...
grouped conditions:

  (CREATE_COIN 0xca13bc2f475ba97fcaed9419e70c8d9350fbe1684ceb36935ad266a8e49fce03 100)

  (AGG_SIG_UNSAFE 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1 "hello chia")
...
================================================================================

aggregated signature check pass: True
pks: [<G1Element a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1>]
msgs: ['68656c6c6f2063686961']
  msg_data: ['']
  coin_ids: ['']
  add_data: ['68656c6c6f2063686961']
signature: 901ae9cbb7a2b795c3c45a0f8ccdd177abee060294e2523a1af64634c89edb15ed873005070d803a637f3c656faead0811ccb624921b9eb30a75f84f4fcc9043c6582b009d94acb4e01d23be1cc535128c04d51ff806544e57641babee148152
None

Public Key/Message Pairs
------------------------
a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1:
        - 68656c6c6f2063686961
```

Everything looks good. Let's push the spend bundle and see if everything works as expected:

```sh
❯ cdv rpc pushtx ./good-sig.json                    
/home/karlkim/kimsk/chia-dev-tools/venv/lib/python3.8/site-packages/chia_blockchain-1.2.11-py3.8.egg/chia/types/spend_bundle.py:96: UserWarning: `coin_solutions` is now `coin_spends` in `SpendBundle.from_json_dict`
  warnings.warn("`coin_solutions` is now `coin_spends` in `SpendBundle.from_json_dict`")
{
    "status": "SUCCESS",
    "success": true
}

❯ cdv rpc coinrecords --by id 17057455729c3ced2be2d07d762a7d18a7b38e66d4bec16c14a4a1dd0a850162
[
    {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x371a8ca374cf53410ed06f7c3c90654394b322cff884890eb78588f33c46e464",
            "puzzle_hash": "0x32632a65eda0d8964cf7a25c900d1545260c544727c128e99aa9074d7992c05e"
        },
        "coinbase": false,
        "confirmed_block_index": 890307,
        "spent": true,
        "spent_block_index": 893372,
        "timestamp": 1637292886
    }
]

❯ cdv rpc coinrecords --by puzhash ca13bc2f475ba97fcaed9419e70c8d9350fbe1684ceb36935ad266a8e49fce03 -s 893000
[
    {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x17057455729c3ced2be2d07d762a7d18a7b38e66d4bec16c14a4a1dd0a850162",
            "puzzle_hash": "0xca13bc2f475ba97fcaed9419e70c8d9350fbe1684ceb36935ad266a8e49fce03"
        },
        "coinbase": false,
        "confirmed_block_index": 893372,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1637350402
    }
]
```

This looks good. Let's try another dummy coin.
Unfortunately, our spend bundle is still not secure because we didn't sign the solution. And bad node can change the `puzzle_hash` in the solution and take all mojos.

To fix this, we have to update our dummy coin code again. This time we will check the signature that sign the `sha256` hash of `new_amount` and `puzzle hash` values.

```lisp
# dfa1bf8b5e100c5b4ebe22f8f534a4d844dfff26eb74cb24809df8c86e78ab82
(mod (
        new_amount
        puzzle_hash
     )

    (include condition_codes.clib)
    (defconstant PUBKEY 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1)

    (list
        (list CREATE_COIN puzzle_hash new_amount)
        (list AGG_SIG_UNSAFE PUBKEY (sha256 new_amount puzzle_hash))
    )
)
```
Here is the code to create a spend bundle.

```python
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

spend_bundle = SpendBundle([dc_spend], sig)
print_json(spend_bundle.to_json_dict(include_legacy_keys = False, exclude_modern_keys = False))
```

If we change any value in the solution after we sign them, the aggregated signature check will not pass.

### AGG_SIG_ME

## Conclusions

We can now make sure that our coin can be spent only if the aggregated signature is valid.


## References
- [chialisp.com | 2 - Coins, Spends and Wallets](https://chialisp.com/docs/coins_spends_and_wallets#bls-aggregated-signatures)
- [chialsip.com | 8 - Security](https://chialisp.com/docs/security)
- [tutorial | 4 - Securing a Smart Coin](https://youtu.be/_SBGfMZhRd8)
- [High Level Tips 1 - Managing State, Coin Creation, Announcements](https://www.youtube.com/watch?v=lDXB4NlbQ-E)
- [High Level Tips 2 - Security, Checking Arguments & Signatures](https://www.youtube.com/watch?v=T4noZyNJkFA)
- [What are BLS Signatures?](https://aggsig.me/signatures.html)
- [BLS Signatures](https://www.marigold.dev/post/bls-signatures)
- [Difference between shamir secret sharing (SSS) vs Multisig vs aggregated signatures (BLS) vs distributed key generation (dkg) vs threshold signatures](https://www.cryptologie.net/article/486/difference-between-shamir-secret-sharing-sss-vs-multisig-vs-aggregated-signatures-bls-vs-distributed-key-generation-dkg-vs-threshold-signatures/)