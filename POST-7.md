# Securing Piggybank Coin (AGG_SIG_ME)

So far, we have been trying to secure piggybank coin system without any digital signature help, but nothing has worked. As we learn about aggregated signature in the [previous post](POST-6.md), let's try to apply what we learn to secure our piggybank coin system.

## Revisit Unsecure Contribution Coin

To deposit to the piggybank coin, we spend contribution coin(s) together with the piggybank coin. The amount of the new piggybank coin will be the amount of the spent piggybank coin and all amount of contribution coin(s) combined.

Let's look at the chialisp code:

```lisp
(mod (my_amount)

    (include condition_codes.clib)

    (defconstant PIGGYBANK_PUZZLE_HASH 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d)

    (list
        (list ASSERT_PUZZLE_ANNOUNCEMENT (sha256 PIGGYBANK_PUZZLE_HASH my_amount))
        (list ASSERT_MY_AMOUNT my_amount)
    )
)
```

To tie contribution coin(s) with a piggybank coin, we use **ANNOUNCEMENT**. And we use `ASSERT_MY_AMOUNT` to make sure that the `my_amount` in the announcement is the same as the amount of the contribution coin itself.

## Add AGG_SIG_ME Condition To Contribution Coin

Now, we can add `AGG_SIG_ME` to only allow a contribution coin to be spent by secret key owner (public key is hard-coded into the puzzle).

```lisp
(mod (my_amount)

    (include condition_codes.clib)

    (defconstant PIGGYBANK_PUZZLE_HASH 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d)
    (defconstant PUBKEY 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1)

    (list
        (list ASSERT_PUZZLE_ANNOUNCEMENT (sha256 PIGGYBANK_PUZZLE_HASH my_amount))
        (list ASSERT_MY_AMOUNT my_amount)
        (list AGG_SIG_ME PUBKEY (sha256 my_amount))
    )
)
```

```sh
❯ cdv rpc coinrecords --by puzhash 0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1 -ou -nd
{
    "0fdf33a1ab85ed0b442d1c2f78c3ffa450ec33036c6da97511e0bf3d268f6749": {
        "coin": {
            "amount": 100000000,
            "parent_coin_info": "0x5ee4d4b849923a65e8c1ed87f8624c4f66654510ed7633b515ebd3d7d0278884",
            "puzzle_hash": "0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1"
        },...
    },
    "ba86adfbbcab04c06109e5dc2702106bac456666dda24c31b0ac10598132467e": {
        "coin": {
            "amount": 200000000,
            "parent_coin_info": "0x6c8a28505d1192e7322b09b1d4a1468e1c4db85e6f2ebfdebc3d83ca53b7f64f",
            "puzzle_hash": "0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1"
        },...
    },...
}

~
❯ cdv rpc coinrecords --by puzhash d02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d -ou -nd
{
    "760f612304a5eb627081632a3c94ef7d4a1aeeaf31e2a29047a6aacb40c0da7b": {
        "coin": {
            "amount": 0,
            "parent_coin_info": "0xa39ffe19087aa846a6cb5c970a92f32366b32b7cfa2772f39005cd11b2e11a7b",
            "puzzle_hash": "0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d"
        },...
    }
}
```

```python
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

spend_bundle = SpendBundle(coin_spends, sig)
print_json(spend_bundle.to_json_dict(include_legacy_keys = False, exclude_modern_keys = False))
```

```json
{
    "aggregated_signature": "0x935a4f17ac0a89d891e585b9c307c18f9cf447ed0a72f8abe8fe7c95973058463f6b5f12109e4b12a2db83d6d7bf045f0a86b9ece04a15d9832e5eb9049f16077eabb4cf3819498ad86c39ae38bb151891389dcff1053a4bfc844f09e79be596",
    "coin_spends": [
        {
            "coin": {
                "amount": 0,
                "parent_coin_info": "0xa39ffe19087aa846a6cb5c970a92f32366b32b7cfa2772f39005cd11b2e11a7b",
                "puzzle_hash": "0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d"
            },
            "puzzle_reveal": "0xff02ffff01ff02ffff03ffff15ffff10ff05ffff02ff3effff04ff02ffff04ff0bff8080808080ff0580ffff01ff02ffff03ffff15ffff10ff05ffff02ff3effff04ff02ffff04ff0bff8080808080ff1a80ffff01ff02ff2effff04ff02ffff04ffff04ffff04ff1cffff04ff14ffff04ffff10ff05ffff02ff3effff04ff02ffff04ff0bff8080808080ff80808080ffff04ffff04ff1cffff04ff17ffff01ff80808080ffff04ffff04ff18ffff04ff17ff808080ffff04ffff04ff10ffff04ff05ff808080ff8080808080ffff04ffff02ff16ffff04ff02ffff04ff0bff80808080ff8080808080ffff01ff02ff2effff04ff02ffff04ffff04ffff04ff1cffff04ff17ffff04ffff10ff05ffff02ff3effff04ff02ffff04ff0bff8080808080ff80808080ffff04ffff04ff18ffff04ff17ff808080ffff04ffff04ff10ffff04ff05ff808080ff80808080ffff04ffff02ff16ffff04ff02ffff04ff0bff80808080ff808080808080ff0180ffff01ff088080ff0180ffff04ffff01ffffff4948ffa0a6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e633ffff3e8201f4ffff02ffff03ffff07ff0580ffff01ff04ffff04ff12ffff04ff09ff808080ffff02ff16ffff04ff02ffff04ff0dff8080808080ff8080ff0180ffff02ffff03ffff07ff0580ffff01ff04ff09ffff02ff2effff04ff02ffff04ff0dffff04ff0bff808080808080ffff010b80ff0180ff02ffff03ffff07ff0580ffff01ff10ff09ffff02ff3effff04ff02ffff04ff0dff8080808080ff8080ff0180ff018080",
            "solution": "0xff80ffff8405f5e100ff840bebc20080ffa0d02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d80"
        },
        {
            "coin": {
                "amount": 100000000,
                "parent_coin_info": "0x5ee4d4b849923a65e8c1ed87f8624c4f66654510ed7633b515ebd3d7d0278884",
                "puzzle_hash": "0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1"
            },
            "puzzle_reveal": "0xff02ffff01ff04ffff04ff0affff04ffff0bff16ff0580ff808080ffff04ffff04ff0cffff04ff05ff808080ffff04ffff04ff08ffff04ff1effff04ffff0bff0580ff80808080ff80808080ffff04ffff01ffff3249ff3fffa0d02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410db0a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1ff018080",
            "solution": "0xff8405f5e10080"
        },
        {
            "coin": {
                "amount": 200000000,
                "parent_coin_info": "0x6c8a28505d1192e7322b09b1d4a1468e1c4db85e6f2ebfdebc3d83ca53b7f64f",
                "puzzle_hash": "0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1"
            },
            "puzzle_reveal": "0xff02ffff01ff04ffff04ff0affff04ffff0bff16ff0580ff808080ffff04ffff04ff0cffff04ff05ff808080ffff04ffff04ff08ffff04ff1effff04ffff0bff0580ff80808080ff80808080ffff04ffff01ffff3249ff3fffa0d02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410db0a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1ff018080",
            "solution": "0xff840bebc20080"
        }
    ]
}
```

```sh
❯ cdv inspect spendbundles ./agg_sig_contribution_coins.json -db -sd                                           
...

Debugging Information
---------------------
================================================================================
consuming coin (0xa39ffe19087aa846a6cb5c970a92f32366b32b7cfa2772f39005cd11b2e11a7b 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d ())
  with id 760f612304a5eb627081632a3c94ef7d4a1aeeaf31e2a29047a6aacb40c0da7b


brun -y main.sym '(a (q 2 (i (> (+ 5 (a 62 (c 2 (c 11 ())))) 5) (q 2 (i (> (+ 5 (a 62 (c 2 (c 11 ())))) 26) (q 2 46 (c 2 (c (c (c 28 (c 20 (c (+ 5 (a 62 (c 2 (c 11 ())))) ()))) (c (c 28 (c 23 (q ()))) (c (c 24 (c 23 ())) (c (c 16 (c 5 ())) ())))) (c (a 22 (c 2 (c 11 ()))) ())))) (q 2 46 (c 2 (c (c (c 28 (c 23 (c (+ 5 (a 62 (c 2 (c 11 ())))) ()))) (c (c 24 (c 23 ())) (c (c 16 (c 5 ())) ()))) (c (a 22 (c 2 (c 11 ()))) ()))))) 1) (q 8)) 1) (c (q ((73 . 72) 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 . 51) (62 . 500) (a (i (l 5) (q 4 (c 18 (c 9 ())) (a 22 (c 2 (c 13 ())))) ()) 1) (a (i (l 5) (q 4 9 (a 46 (c 2 (c 13 (c 11 ()))))) (q . 11)) 1) 2 (i (l 5) (q 16 9 (a 62 (c 2 (c 13 ())))) ()) 1) 1))' '(() (0x05f5e100 0x0bebc200) 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d)'

((CREATE_COIN 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 0x11e1a300) (CREATE_COIN 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d ()) (ASSERT_MY_PUZZLEHASH 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d) (ASSERT_MY_AMOUNT ()) (CREATE_PUZZLE_ANNOUNCEMENT 0x05f5e100) (CREATE_PUZZLE_ANNOUNCEMENT 0x0bebc200))

grouped conditions:

  (CREATE_COIN 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 0x11e1a300)
  (CREATE_COIN 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d ())

  (ASSERT_MY_PUZZLEHASH 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d)

  (ASSERT_MY_AMOUNT ())

  (CREATE_PUZZLE_ANNOUNCEMENT 0x05f5e100)
  (CREATE_PUZZLE_ANNOUNCEMENT 0x0bebc200)


-------
consuming coin (0x5ee4d4b849923a65e8c1ed87f8624c4f66654510ed7633b515ebd3d7d0278884 0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1 0x05f5e100)
  with id 0fdf33a1ab85ed0b442d1c2f78c3ffa450ec33036c6da97511e0bf3d268f6749


brun -y main.sym '(a (q 4 (c 10 (c (sha256 22 5) ())) (c (c 12 (c 5 ())) (c (c 8 (c 30 (c (sha256 5) ()))) ()))) (c (q (50 . 73) 63 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d . 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1) 1))' '(0x05f5e100)'

((ASSERT_PUZZLE_ANNOUNCEMENT 0x5d84a960d3d702408add0bc8702c1a80ce38d78c27880297600143105c13ca49) (ASSERT_MY_AMOUNT 0x05f5e100) (AGG_SIG_ME 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1 0x547b7dbafa7395a48f9514232ae6e1abfbaff85eafc08413b8276839ff11e28a))

grouped conditions:

  (ASSERT_PUZZLE_ANNOUNCEMENT 0x5d84a960d3d702408add0bc8702c1a80ce38d78c27880297600143105c13ca49)

  (ASSERT_MY_AMOUNT 0x05f5e100)

  (AGG_SIG_ME 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1 0x547b7dbafa7395a48f9514232ae6e1abfbaff85eafc08413b8276839ff11e28a)


-------
consuming coin (0x6c8a28505d1192e7322b09b1d4a1468e1c4db85e6f2ebfdebc3d83ca53b7f64f 0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1 0x0bebc200)
  with id ba86adfbbcab04c06109e5dc2702106bac456666dda24c31b0ac10598132467e


brun -y main.sym '(a (q 4 (c 10 (c (sha256 22 5) ())) (c (c 12 (c 5 ())) (c (c 8 (c 30 (c (sha256 5) ()))) ()))) (c (q (50 . 73) 63 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d . 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1) 1))' '(0x0bebc200)'

((ASSERT_PUZZLE_ANNOUNCEMENT 0x35fa1879d45acfcecd3faea89a81a7e4017a029e2b25fa0d2afe823d7a1f3a39) (ASSERT_MY_AMOUNT 0x0bebc200) (AGG_SIG_ME 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1 0x4330e95ffd415c7f160c19ce627108094ed99b8d16544f90327cc7903d4e09ce))

grouped conditions:

  (ASSERT_PUZZLE_ANNOUNCEMENT 0x35fa1879d45acfcecd3faea89a81a7e4017a029e2b25fa0d2afe823d7a1f3a39)

  (ASSERT_MY_AMOUNT 0x0bebc200)

  (AGG_SIG_ME 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1 0x4330e95ffd415c7f160c19ce627108094ed99b8d16544f90327cc7903d4e09ce)


-------

spent coins
  (0x5ee4d4b849923a65e8c1ed87f8624c4f66654510ed7633b515ebd3d7d0278884 0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1 0x05f5e100)
      => spent coin id 0fdf33a1ab85ed0b442d1c2f78c3ffa450ec33036c6da97511e0bf3d268f6749
  (0xa39ffe19087aa846a6cb5c970a92f32366b32b7cfa2772f39005cd11b2e11a7b 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d ())
      => spent coin id 760f612304a5eb627081632a3c94ef7d4a1aeeaf31e2a29047a6aacb40c0da7b
  (0x6c8a28505d1192e7322b09b1d4a1468e1c4db85e6f2ebfdebc3d83ca53b7f64f 0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1 0x0bebc200)
      => spent coin id ba86adfbbcab04c06109e5dc2702106bac456666dda24c31b0ac10598132467e

created coins
  (0x760f612304a5eb627081632a3c94ef7d4a1aeeaf31e2a29047a6aacb40c0da7b 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 0x11e1a300)
      => created coin id 6b524331b769daec2331dbc9b943d8a037459a00cae91d2516916e64f743fe30
  (0x760f612304a5eb627081632a3c94ef7d4a1aeeaf31e2a29047a6aacb40c0da7b 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d ())
      => created coin id 9a1c86f46a4bac9069372eecb25dbce63642c2aee9d6497c95244db3dbc5800f
created puzzle announcements
  ['0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d', '0x0bebc200'] =>
      35fa1879d45acfcecd3faea89a81a7e4017a029e2b25fa0d2afe823d7a1f3a39
  ['0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d', '0x05f5e100'] =>
      5d84a960d3d702408add0bc8702c1a80ce38d78c27880297600143105c13ca49


zero_coin_set = [<bytes32: 9a1c86f46a4bac9069372eecb25dbce63642c2aee9d6497c95244db3dbc5800f>]

created  puzzle announcements = ['35fa1879d45acfcecd3faea89a81a7e4017a029e2b25fa0d2afe823d7a1f3a39', '5d84a960d3d702408add0bc8702c1a80ce38d78c27880297600143105c13ca49']

asserted puzzle announcements = ['35fa1879d45acfcecd3faea89a81a7e4017a029e2b25fa0d2afe823d7a1f3a39', '5d84a960d3d702408add0bc8702c1a80ce38d78c27880297600143105c13ca49']

symdiff of puzzle announcements = []


================================================================================

aggregated signature check pass: True
pks: [<G1Element a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1>, <G1Element a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1>]
msgs: ['547b7dbafa7395a48f9514232ae6e1abfbaff85eafc08413b8276839ff11e28a0fdf33a1ab85ed0b442d1c2f78c3ffa450ec33036c6da97511e0bf3d268f6749ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb', '4330e95ffd415c7f160c19ce627108094ed99b8d16544f90327cc7903d4e09ceba86adfbbcab04c06109e5dc2702106bac456666dda24c31b0ac10598132467eccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb']
  msg_data: ['547b7dbafa7395a48f9514232ae6e1abfbaff85eafc08413b8276839ff11e28a', '4330e95ffd415c7f160c19ce627108094ed99b8d16544f90327cc7903d4e09ce']
  coin_ids: ['0fdf33a1ab85ed0b442d1c2f78c3ffa450ec33036c6da97511e0bf3d268f6749', 'ba86adfbbcab04c06109e5dc2702106bac456666dda24c31b0ac10598132467e']
  add_data: ['ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb', 'ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb']
signature: 935a4f17ac0a89d891e585b9c307c18f9cf447ed0a72f8abe8fe7c95973058463f6b5f12109e4b12a2db83d6d7bf045f0a86b9ece04a15d9832e5eb9049f16077eabb4cf3819498ad86c39ae38bb151891389dcff1053a4bfc844f09e79be596
None

Public Key/Message Pairs
------------------------
a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1:
        - 547b7dbafa7395a48f9514232ae6e1abfbaff85eafc08413b8276839ff11e28a0fdf33a1ab85ed0b442d1c2f78c3ffa450ec33036c6da97511e0bf3d268f6749ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb
        - 4330e95ffd415c7f160c19ce627108094ed99b8d16544f90327cc7903d4e09ceba86adfbbcab04c06109e5dc2702106bac456666dda24c31b0ac10598132467eccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb
```

The example above shows two contribution coins with the amount of 100 and 200 million mojos are spent and 300 million mojos coin is created.

```sh
❯ cdv rpc coinrecords --by puzhash 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 -ou
[
    ...
    {
        "coin": {
            "amount": 300000000,
            "parent_coin_info": "0x760f612304a5eb627081632a3c94ef7d4a1aeeaf31e2a29047a6aacb40c0da7b",
            "puzzle_hash": "0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6"
        },...
    }
]
```

## ANNOUNCEMENT issue

In the previous post, we have the [announcement issue](https://github.com/kimsk/chia-piggybank/blob/main/POST-5.md#announcement-gotcha). Adding `AGG_SIG_ME` also resolve the problem.

Let's see some example.

```sh
❯ cdv rpc coinrecords --by puzhash 0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1 -ou -nd
# contribution coins
{
    "032380717266e352532856bc3cdb37cdb0e086b9e7eb3121e774f213dafd40a1": {
        "coin": {
            "amount": 100000000,
            "parent_coin_info": "0x4b32bb0a40580f05b601165641d5713334add92e4474294293cb2d52d0653442",
            "puzzle_hash": "0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1"
        },...
    },
    "b2b6063600b339ca233f62bd3b0766ef00b4b28d784f0f61f020fbfc1d621c37": {
        "coin": {
            "amount": 300000000,
            "parent_coin_info": "0x65133f8b02e56d24e4a551ecf10de2b2bc2bcc9c4a0d59fd82b48062a1ab59f7",
            "puzzle_hash": "0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1"
        },...
    },
    "f364b35f232bb057a08e7c7afc353cbb274456fa8b2cbf9579c1e6d96f8c9894": {
        "coin": {
            "amount": 100000000,
            "parent_coin_info": "0x224cec5387bd032fd0cf5daf8bbf888b18af2af878f2a417f5733ddc681cda1a",
            "puzzle_hash": "0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1"
        },...
    }
}

# piggybank coin
❯ cdv rpc coinrecords --by puzhash d02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d -ou -nd
{
    "9a1c86f46a4bac9069372eecb25dbce63642c2aee9d6497c95244db3dbc5800f": {
        "coin": {
            "amount": 0,
            "parent_coin_info": "0x760f612304a5eb627081632a3c94ef7d4a1aeeaf31e2a29047a6aacb40c0da7b",
            "puzzle_hash": "0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d"
        },...
    }
}
```

```python
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
```

```sh
❯ cdv inspect spendbundles ./agg_sig_contribution_coins-bad.json -db -sd                     
[{"aggregated_signature": "0x8143ed61dfac1bd90c29d4d12a7b9f77b56e195f4cb6acf67c36fd341093d7946af284e9a1b5052f340fdf052f7a51ea02c87ef4425d24a124d00c140c35c2cff4b6b8903b83b6121f042c61a47a47c9d6b8bb9dd297c63616c9b90ef0390703", "coin_solutions": [{"coin": {"parent_coin_info": "0x760f612304a5eb627081632a3c94ef7d4a1aeeaf31e2a29047a6aacb40c0da7b", "puzzle_hash": "0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d", "amount": 0}, "puzzle_reveal": "0xff02ffff01ff02ffff03ffff15ffff10ff05ffff02ff3effff04ff02ffff04ff0bff8080808080ff0580ffff01ff02ffff03ffff15ffff10ff05ffff02ff3effff04ff02ffff04ff0bff8080808080ff1a80ffff01ff02ff2effff04ff02ffff04ffff04ffff04ff1cffff04ff14ffff04ffff10ff05ffff02ff3effff04ff02ffff04ff0bff8080808080ff80808080ffff04ffff04ff1cffff04ff17ffff01ff80808080ffff04ffff04ff18ffff04ff17ff808080ffff04ffff04ff10ffff04ff05ff808080ff8080808080ffff04ffff02ff16ffff04ff02ffff04ff0bff80808080ff8080808080ffff01ff02ff2effff04ff02ffff04ffff04ffff04ff1cffff04ff17ffff04ffff10ff05ffff02ff3effff04ff02ffff04ff0bff8080808080ff80808080ffff04ffff04ff18ffff04ff17ff808080ffff04ffff04ff10ffff04ff05ff808080ff80808080ffff04ffff02ff16ffff04ff02ffff04ff0bff80808080ff808080808080ff0180ffff01ff088080ff0180ffff04ffff01ffffff4948ffa0a6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e633ffff3e8201f4ffff02ffff03ffff07ff0580ffff01ff04ffff04ff12ffff04ff09ff808080ffff02ff16ffff04ff02ffff04ff0dff8080808080ff8080ff0180ffff02ffff03ffff07ff0580ffff01ff04ff09ffff02ff2effff04ff02ffff04ff0dffff04ff0bff808080808080ffff010b80ff0180ff02ffff03ffff07ff0580ffff01ff10ff09ffff02ff3effff04ff02ffff04ff0dff8080808080ff8080ff0180ff018080", "solution": "0xff80ffff8405f5e100ff8411e1a30080ffa0d02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d80"}, {"coin": {"parent_coin_info": "0x4b32bb0a40580f05b601165641d5713334add92e4474294293cb2d52d0653442", "puzzle_hash": "0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1", "amount": 100000000}, "puzzle_reveal": "0xff02ffff01ff04ffff04ff0affff04ffff0bff16ff0580ff808080ffff04ffff04ff0cffff04ff05ff808080ffff04ffff04ff08ffff04ff1effff04ffff0bff0580ff80808080ff80808080ffff04ffff01ffff3249ff3fffa0d02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410db0a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1ff018080", "solution": "0xff8405f5e10080"}, {"coin": {"parent_coin_info": "0x65133f8b02e56d24e4a551ecf10de2b2bc2bcc9c4a0d59fd82b48062a1ab59f7", "puzzle_hash": "0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1", "amount": 300000000}, "puzzle_reveal": "0xff02ffff01ff04ffff04ff0affff04ffff0bff16ff0580ff808080ffff04ffff04ff0cffff04ff05ff808080ffff04ffff04ff08ffff04ff1effff04ffff0bff0580ff80808080ff80808080ffff04ffff01ffff3249ff3fffa0d02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410db0a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1ff018080", "solution": "0xff8411e1a30080"}, {"coin": {"parent_coin_info": "0x224cec5387bd032fd0cf5daf8bbf888b18af2af878f2a417f5733ddc681cda1a", "puzzle_hash": "0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1", "amount": 100000000}, "puzzle_reveal": "0xff02ffff01ff04ffff04ff0affff04ffff0bff16ff0580ff808080ffff04ffff04ff0cffff04ff05ff808080ffff04ffff04ff08ffff04ff1effff04ffff0bff0580ff80808080ff80808080ffff04ffff01ffff3249ff3fffa0d02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410db0a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1ff018080", "solution": "0xff8405f5e10080"}]}]

Debugging Information
---------------------
================================================================================
consuming coin (0x760f612304a5eb627081632a3c94ef7d4a1aeeaf31e2a29047a6aacb40c0da7b 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d ())
  with id 9a1c86f46a4bac9069372eecb25dbce63642c2aee9d6497c95244db3dbc5800f


brun -y main.sym '(a (q 2 (i (> (+ 5 (a 62 (c 2 (c 11 ())))) 5) (q 2 (i (> (+ 5 (a 62 (c 2 (c 11 ())))) 26) (q 2 46 (c 2 (c (c (c 28 (c 20 (c (+ 5 (a 62 (c 2 (c 11 ())))) ()))) (c (c 28 (c 23 (q ()))) (c (c 24 (c 23 ())) (c (c 16 (c 5 ())) ())))) (c (a 22 (c 2 (c 11 ()))) ())))) (q 2 46 (c 2 (c (c (c 28 (c 23 (c (+ 5 (a 62 (c 2 (c 11 ())))) ()))) (c (c 24 (c 23 ())) (c (c 16 (c 5 ())) ()))) (c (a 22 (c 2 (c 11 ()))) ()))))) 1) (q 8)) 1) (c (q ((73 . 72) 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 . 51) (62 . 500) (a (i (l 5) (q 4 (c 18 (c 9 ())) (a 22 (c 2 (c 13 ())))) ()) 1) (a (i (l 5) (q 4 9 (a 46 (c 2 (c 13 (c 11 ()))))) (q . 11)) 1) 2 (i (l 5) (q 16 9 (a 62 (c 2 (c 13 ())))) ()) 1) 1))' '(() (0x05f5e100 0x11e1a300) 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d)'

((CREATE_COIN 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 0x17d78400) (CREATE_COIN 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d ()) (ASSERT_MY_PUZZLEHASH 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d) (ASSERT_MY_AMOUNT ()) (CREATE_PUZZLE_ANNOUNCEMENT 0x05f5e100) (CREATE_PUZZLE_ANNOUNCEMENT 0x11e1a300))

grouped conditions:

  (CREATE_COIN 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 0x17d78400)
  (CREATE_COIN 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d ())

  (ASSERT_MY_PUZZLEHASH 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d)

  (ASSERT_MY_AMOUNT ())

  (CREATE_PUZZLE_ANNOUNCEMENT 0x05f5e100)
  (CREATE_PUZZLE_ANNOUNCEMENT 0x11e1a300)


-------
consuming coin (0x4b32bb0a40580f05b601165641d5713334add92e4474294293cb2d52d0653442 0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1 0x05f5e100)
  with id 032380717266e352532856bc3cdb37cdb0e086b9e7eb3121e774f213dafd40a1


brun -y main.sym '(a (q 4 (c 10 (c (sha256 22 5) ())) (c (c 12 (c 5 ())) (c (c 8 (c 30 (c (sha256 5) ()))) ()))) (c (q (50 . 73) 63 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d . 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1) 1))' '(0x05f5e100)'

((ASSERT_PUZZLE_ANNOUNCEMENT 0x5d84a960d3d702408add0bc8702c1a80ce38d78c27880297600143105c13ca49) (ASSERT_MY_AMOUNT 0x05f5e100) (AGG_SIG_ME 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1 0x547b7dbafa7395a48f9514232ae6e1abfbaff85eafc08413b8276839ff11e28a))

grouped conditions:

  (ASSERT_PUZZLE_ANNOUNCEMENT 0x5d84a960d3d702408add0bc8702c1a80ce38d78c27880297600143105c13ca49)

  (ASSERT_MY_AMOUNT 0x05f5e100)

  (AGG_SIG_ME 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1 0x547b7dbafa7395a48f9514232ae6e1abfbaff85eafc08413b8276839ff11e28a)


-------
consuming coin (0x65133f8b02e56d24e4a551ecf10de2b2bc2bcc9c4a0d59fd82b48062a1ab59f7 0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1 0x11e1a300)
  with id b2b6063600b339ca233f62bd3b0766ef00b4b28d784f0f61f020fbfc1d621c37


brun -y main.sym '(a (q 4 (c 10 (c (sha256 22 5) ())) (c (c 12 (c 5 ())) (c (c 8 (c 30 (c (sha256 5) ()))) ()))) (c (q (50 . 73) 63 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d . 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1) 1))' '(0x11e1a300)'

((ASSERT_PUZZLE_ANNOUNCEMENT 0xae0a8d30bb07d578a4482ce64756d310dd62cd34469727564e3affcf04192180) (ASSERT_MY_AMOUNT 0x11e1a300) (AGG_SIG_ME 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1 0x30dd4a7cd60b12138663ca508f001c97263c1c687befb687ce5ae9d92e54044b))

grouped conditions:

  (ASSERT_PUZZLE_ANNOUNCEMENT 0xae0a8d30bb07d578a4482ce64756d310dd62cd34469727564e3affcf04192180)

  (ASSERT_MY_AMOUNT 0x11e1a300)

  (AGG_SIG_ME 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1 0x30dd4a7cd60b12138663ca508f001c97263c1c687befb687ce5ae9d92e54044b)


-------
consuming coin (0x224cec5387bd032fd0cf5daf8bbf888b18af2af878f2a417f5733ddc681cda1a 0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1 0x05f5e100)
  with id f364b35f232bb057a08e7c7afc353cbb274456fa8b2cbf9579c1e6d96f8c9894


brun -y main.sym '(a (q 4 (c 10 (c (sha256 22 5) ())) (c (c 12 (c 5 ())) (c (c 8 (c 30 (c (sha256 5) ()))) ()))) (c (q (50 . 73) 63 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d . 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1) 1))' '(0x05f5e100)'

((ASSERT_PUZZLE_ANNOUNCEMENT 0x5d84a960d3d702408add0bc8702c1a80ce38d78c27880297600143105c13ca49) (ASSERT_MY_AMOUNT 0x05f5e100) (AGG_SIG_ME 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1 0x547b7dbafa7395a48f9514232ae6e1abfbaff85eafc08413b8276839ff11e28a))

grouped conditions:

  (ASSERT_PUZZLE_ANNOUNCEMENT 0x5d84a960d3d702408add0bc8702c1a80ce38d78c27880297600143105c13ca49)

  (ASSERT_MY_AMOUNT 0x05f5e100)

  (AGG_SIG_ME 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1 0x547b7dbafa7395a48f9514232ae6e1abfbaff85eafc08413b8276839ff11e28a)


-------

spent coins
  (0x4b32bb0a40580f05b601165641d5713334add92e4474294293cb2d52d0653442 0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1 0x05f5e100)
      => spent coin id 032380717266e352532856bc3cdb37cdb0e086b9e7eb3121e774f213dafd40a1
  (0x760f612304a5eb627081632a3c94ef7d4a1aeeaf31e2a29047a6aacb40c0da7b 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d ())
      => spent coin id 9a1c86f46a4bac9069372eecb25dbce63642c2aee9d6497c95244db3dbc5800f
  (0x65133f8b02e56d24e4a551ecf10de2b2bc2bcc9c4a0d59fd82b48062a1ab59f7 0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1 0x11e1a300)
      => spent coin id b2b6063600b339ca233f62bd3b0766ef00b4b28d784f0f61f020fbfc1d621c37
  (0x224cec5387bd032fd0cf5daf8bbf888b18af2af878f2a417f5733ddc681cda1a 0xbd21ffef9bba7064f842a1f62601bdf6016f45f9d9e5ef4bbbc0263151642bf1 0x05f5e100)
      => spent coin id f364b35f232bb057a08e7c7afc353cbb274456fa8b2cbf9579c1e6d96f8c9894

created coins
  (0x9a1c86f46a4bac9069372eecb25dbce63642c2aee9d6497c95244db3dbc5800f 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d ())
      => created coin id 118e1ff10ba4ca38598f144c74bbfc68127abf608e20209fa66796ea6c79a0a7
  (0x9a1c86f46a4bac9069372eecb25dbce63642c2aee9d6497c95244db3dbc5800f 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 0x17d78400)
      => created coin id a22d6bdcd1a4ecc0aff6524435e378d7dc0e7de49028521525a648b17482e6df
created puzzle announcements
  ['0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d', '0x05f5e100'] =>
      5d84a960d3d702408add0bc8702c1a80ce38d78c27880297600143105c13ca49
  ['0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d', '0x11e1a300'] =>
      ae0a8d30bb07d578a4482ce64756d310dd62cd34469727564e3affcf04192180


zero_coin_set = [<bytes32: 118e1ff10ba4ca38598f144c74bbfc68127abf608e20209fa66796ea6c79a0a7>]

created  puzzle announcements = ['5d84a960d3d702408add0bc8702c1a80ce38d78c27880297600143105c13ca49', 'ae0a8d30bb07d578a4482ce64756d310dd62cd34469727564e3affcf04192180']

asserted puzzle announcements = ['5d84a960d3d702408add0bc8702c1a80ce38d78c27880297600143105c13ca49', '5d84a960d3d702408add0bc8702c1a80ce38d78c27880297600143105c13ca49', 'ae0a8d30bb07d578a4482ce64756d310dd62cd34469727564e3affcf04192180']

symdiff of puzzle announcements = []


================================================================================

aggregated signature check pass: True
pks: [<G1Element a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1>, <G1Element a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1>, <G1Element a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1>]
msgs: ['547b7dbafa7395a48f9514232ae6e1abfbaff85eafc08413b8276839ff11e28a032380717266e352532856bc3cdb37cdb0e086b9e7eb3121e774f213dafd40a1ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb', '30dd4a7cd60b12138663ca508f001c97263c1c687befb687ce5ae9d92e54044bb2b6063600b339ca233f62bd3b0766ef00b4b28d784f0f61f020fbfc1d621c37ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb', '547b7dbafa7395a48f9514232ae6e1abfbaff85eafc08413b8276839ff11e28af364b35f232bb057a08e7c7afc353cbb274456fa8b2cbf9579c1e6d96f8c9894ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb']
  msg_data: ['547b7dbafa7395a48f9514232ae6e1abfbaff85eafc08413b8276839ff11e28a', '30dd4a7cd60b12138663ca508f001c97263c1c687befb687ce5ae9d92e54044b', '547b7dbafa7395a48f9514232ae6e1abfbaff85eafc08413b8276839ff11e28a']
  coin_ids: ['032380717266e352532856bc3cdb37cdb0e086b9e7eb3121e774f213dafd40a1', 'b2b6063600b339ca233f62bd3b0766ef00b4b28d784f0f61f020fbfc1d621c37', 'f364b35f232bb057a08e7c7afc353cbb274456fa8b2cbf9579c1e6d96f8c9894']
  add_data: ['ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb', 'ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb', 'ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb']
signature: 8143ed61dfac1bd90c29d4d12a7b9f77b56e195f4cb6acf67c36fd341093d7946af284e9a1b5052f340fdf052f7a51ea02c87ef4425d24a124d00c140c35c2cff4b6b8903b83b6121f042c61a47a47c9d6b8bb9dd297c63616c9b90ef0390703
None

Public Key/Message Pairs
------------------------
a0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1:
        - 547b7dbafa7395a48f9514232ae6e1abfbaff85eafc08413b8276839ff11e28a032380717266e352532856bc3cdb37cdb0e086b9e7eb3121e774f213dafd40a1ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb
        - 30dd4a7cd60b12138663ca508f001c97263c1c687befb687ce5ae9d92e54044bb2b6063600b339ca233f62bd3b0766ef00b4b28d784f0f61f020fbfc1d621c37ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb
        - 547b7dbafa7395a48f9514232ae6e1abfbaff85eafc08413b8276839ff11e28af364b35f232bb057a08e7c7afc353cbb274456fa8b2cbf9579c1e6d96f8c9894ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb
```

```sh
❯ cdv rpc coinrecords --by puzhash 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 -ou
[
    ...
    {
        "coin": {
            "amount": 400000000,
            "parent_coin_info": "0x9a1c86f46a4bac9069372eecb25dbce63642c2aee9d6497c95244db3dbc5800f",
            "puzzle_hash": "0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6"
        },
        "coinbase": false,
        "confirmed_block_index": 904491,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1637559009
    }
]

❯ cdv rpc blockrecords -i 904491
{
    ...
    "fees": 100000000,
    ...
    "header_hash": "0x3a18773fe0ed5dcf3ccec92c5f56b207c5324cf4be1077c768a2c3f6e97f9e37",
    "height": 904491,
    ...
}
```

As we can see, it still doesn't solve the announcement issue.

## Conclusions

Now our contribution coins can only be spent by a user with a designated secret key. Next post, we will try to resolve the announcement issue by including coin id in the message.
