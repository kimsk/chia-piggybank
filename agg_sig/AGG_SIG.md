```lisp
(mod (
        my_amount
        to_puzzle_hash
        agg_pk
     )

    (include condition_codes.clib)

    (list
        (list CREATE_COIN to_puzzle_hash my_amount)
        (list ASSERT_MY_AMOUNT my_amount)
        (list AGG_SIG_ME agg_pk (sha256 my_amount))
    )
)
```

```sh
❯ brun (run ./agg_sig_coin.clsp -i ../include) '(100 0xcafef00d (01 02 03))' -c --time      
cost = 1952
assemble_from_ir: 0.015848
to_sexp_f: 0.000337
run_program: 0.001884
((51 0xcafef00d 100) (73 100) (50 (q 2 3) 0x18ac3e7343f016890c510e93f935261169d9e3f565436429830faf0934f4f8e4))
```

```python
network: Network = asyncio.run(Network.create())
asyncio.run(network.farm_block())
alice: Wallet = network.make_wallet("alice")
bob: Wallet = network.make_wallet("bob")
owner1: Wallet = network.make_wallet("owner1")
owner2: Wallet = network.make_wallet("owner2")
asyncio.run(network.farm_block(farmer=alice))
print(len(alice.usable_coins))
print(alice.balance())


AGG_SIG_COIN = load_clvm("agg_sig_coin.clsp", package_or_requirement=__name__, search_paths=["../include"])
print(AGG_SIG_COIN.get_tree_hash())

amt = 1000000000000
agg_sig_coin = asyncio.run(alice.launch_smart_coin(AGG_SIG_COIN, amt=amt))
print(agg_sig_coin.as_coin())

agg_pk = owner1.pk() + owner2.pk()

agg_sig_coin_solution = Program.to([amt, bob.puzzle_hash, agg_pk])

spend = CoinSpend(
    agg_sig_coin.as_coin(),
    AGG_SIG_COIN,
    agg_sig_coin_solution 
)

sk1: PrivateKey = owner1.pk_to_sk(owner1.pk())
sk2: PrivateKey = owner2.pk_to_sk(owner2.pk())
message: bytes = std_hash(int_to_bytes(agg_sig_coin.amount))
sig1: G2Element = AugSchemeMPL.sign(sk1,
                    message
                    + agg_sig_coin.name()
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA,
                    agg_pk
                )

sig2: G2Element = AugSchemeMPL.sign(sk2,
                    message
                    + agg_sig_coin.name()
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA,
                    agg_pk
                )

agg_sig = AugSchemeMPL.aggregate([sig1, sig2])

assert AugSchemeMPL.verify(agg_pk,
                    message
                    + agg_sig_coin.name()
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA,
                    agg_sig)

spend_bundle = SpendBundle([spend], agg_sig)
print(spend_bundle)

print(bob.balance())
asyncio.run(network.push_tx(spend_bundle))
print(bob.balance())

asyncio.run(network.close())

print_json(spend_bundle.to_json_dict(include_legacy_keys = False, exclude_modern_keys = False))
```

```sh
❯ cdv inspect spendbundles ./agg_sig_coin.json -db -sd
[{"aggregated_signature": "0xb479d33b8bb20de753ac3b2aa7ce28f4c6a365f5602e714e07c13bf73119c2763230d577a995f2e9243af93eb872068a0e98a6acd1d2b74068acb6295a18e6616a849bddb172e12f28bfd3e38f184ba4cd3869d399287b44d833c5f96c30bfad", "coin_solutions": [{"coin": {"parent_coin_info": "0x8d011a3236082916e08a2214379a063b38a8c7c2ed7fb6a708acf824e1d9b310", "puzzle_hash": "0x35dd7bf62d31b380e56a38d5043454642bf89610ec1b50b0aa2c5e1ab3490a78", "amount": 1000000000000}, "puzzle_reveal": "0xff02ffff01ff04ffff04ff0effff04ff0bffff04ff05ff80808080ffff04ffff04ff0affff04ff05ff808080ffff04ffff04ff04ffff04ff17ffff04ffff0bff0580ff80808080ff80808080ffff04ffff01ff32ff4933ff018080", "solution": "0xff8600e8d4a51000ffa05abb5d5568b4a7411dd97b3356cfedfac09b5fb35621a7fa29ab9b59dc905fb6ffb0a1c3ab75cc3901f665f507a94df4c2a57789155eb8d6835d5eccc6752b2fdb40bd39752722e068298b0b3710acb730df80"}]}]

Debugging Information
---------------------
================================================================================
consuming coin (0x8d011a3236082916e08a2214379a063b38a8c7c2ed7fb6a708acf824e1d9b310 0x35dd7bf62d31b380e56a38d5043454642bf89610ec1b50b0aa2c5e1ab3490a78 0x00e8d4a51000)
  with id fce0f70488480693515ad997642c81253dc4af75230b9f4e70ba8108f1844776


brun -y main.sym '(a (q 4 (c 14 (c 11 (c 5 ()))) (c (c 10 (c 5 ())) (c (c 4 (c 23 (c (sha256 5) ()))) ()))) (c (q 50 73 . 51) 1))' '(0x00e8d4a51000 0x5abb5d5568b4a7411dd97b3356cfedfac09b5fb35621a7fa29ab9b59dc905fb6 0xa1c3ab75cc3901f665f507a94df4c2a57789155eb8d6835d5eccc6752b2fdb40bd39752722e068298b0b3710acb730df)'

((CREATE_COIN 0x5abb5d5568b4a7411dd97b3356cfedfac09b5fb35621a7fa29ab9b59dc905fb6 0x00e8d4a51000) (ASSERT_MY_AMOUNT 0x00e8d4a51000) (AGG_SIG_ME 0xa1c3ab75cc3901f665f507a94df4c2a57789155eb8d6835d5eccc6752b2fdb40bd39752722e068298b0b3710acb730df 0x19b6f428a262c387186c195922d543d88492ba7d83f204d5a03f2004d741b86c))

grouped conditions:

  (CREATE_COIN 0x5abb5d5568b4a7411dd97b3356cfedfac09b5fb35621a7fa29ab9b59dc905fb6 0x00e8d4a51000)

  (ASSERT_MY_AMOUNT 0x00e8d4a51000)

  (AGG_SIG_ME 0xa1c3ab75cc3901f665f507a94df4c2a57789155eb8d6835d5eccc6752b2fdb40bd39752722e068298b0b3710acb730df 0x19b6f428a262c387186c195922d543d88492ba7d83f204d5a03f2004d741b86c)


-------

spent coins
  (0x8d011a3236082916e08a2214379a063b38a8c7c2ed7fb6a708acf824e1d9b310 0x35dd7bf62d31b380e56a38d5043454642bf89610ec1b50b0aa2c5e1ab3490a78 0x00e8d4a51000)
      => spent coin id fce0f70488480693515ad997642c81253dc4af75230b9f4e70ba8108f1844776

created coins
  (0xfce0f70488480693515ad997642c81253dc4af75230b9f4e70ba8108f1844776 0x5abb5d5568b4a7411dd97b3356cfedfac09b5fb35621a7fa29ab9b59dc905fb6 0x00e8d4a51000)
      => created coin id 56450223c2351ff9030c9532afe00680a82bd72df9ab51c92221ce40b48c7a38


zero_coin_set = []


================================================================================

aggregated signature check pass: True
pks: [<G1Element a1c3ab75cc3901f665f507a94df4c2a57789155eb8d6835d5eccc6752b2fdb40bd39752722e068298b0b3710acb730df>]
msgs: ['19b6f428a262c387186c195922d543d88492ba7d83f204d5a03f2004d741b86cfce0f70488480693515ad997642c81253dc4af75230b9f4e70ba8108f1844776ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb']
  msg_data: ['19b6f428a262c387186c195922d543d88492ba7d83f204d5a03f2004d741b86c']
  coin_ids: ['fce0f70488480693515ad997642c81253dc4af75230b9f4e70ba8108f1844776']
  add_data: ['ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb']
signature: b479d33b8bb20de753ac3b2aa7ce28f4c6a365f5602e714e07c13bf73119c2763230d577a995f2e9243af93eb872068a0e98a6acd1d2b74068acb6295a18e6616a849bddb172e12f28bfd3e38f184ba4cd3869d399287b44d833c5f96c30bfad
None

Public Key/Message Pairs
------------------------
a1c3ab75cc3901f665f507a94df4c2a57789155eb8d6835d5eccc6752b2fdb40bd39752722e068298b0b3710acb730df:
        - 19b6f428a262c387186c195922d543d88492ba7d83f204d5a03f2004d741b86cfce0f70488480693515ad997642c81253dc4af75230b9f4e70ba8108f1844776ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb
```
