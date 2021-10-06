# Securing Piggybank Coin (ANNOUCEMENT)

> [Money ain’t got no owners, just spenders](https://www.youtube.com/watch?v=PT2I1T87nwQ&t=133s) - Omar Little | The Wire


In Chia, there is no concept of coin ownership as the wallet address is actually a [bech32m decoded puzzle hash](https://www.chiaexplorer.com/tools/address-puzzlehash-converter). So our puzzle has to be able to prevent the coin to be spent unintentionally. We have been coding our smart coins in chialisp and the driver code in python to make it easier to deploy/spend those coins. However, there is nothing to prevent other people to [spend](https://chialisp.com/docs/coins_spends_and_wallets#spends) our coins.


## Steal Contribution Coins

Let's look at our contribution coin's puzzle again:

```lisp
()
```

### Steal With A Dummy Coin

Our puzzle does nothing at all, so anyone could easily scan the blockchain and spend those coins by bundle them together with a simple coin that just create a new coin:

```lisp
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

The malicious user can create a spend bundle with a contribution coin and a dummy coin  and provide a puzzle hash to which mojos will be sent. Here is the spend bundles that will steal 100 mojos of contribution coin:
```json
{
    "aggregated_signature": "0xc00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "coin_solutions": [
        {
            "coin": {
                "amount": 100,
                "parent_coin_info": "0x9c421f8f7c0d9d8df1483b960bfd83c4994b2bfbcd29470c983774c09b7be8d4",
                "puzzle_hash": "0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a"
            },
            "puzzle_reveal": "0x80",
            "solution": "0x80"
        },
        {
            "coin": {
                "amount": 0,
                "parent_coin_info": "0x15c5d04550d6d393529101e24675ffc059b89514f0d156145fa9ab6d24cc905a",
                "puzzle_hash": "0xb92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd"
            },
            "puzzle_reveal": "0xff02ffff01ff04ffff04ff02ffff04ff0bffff04ff05ff80808080ff8080ffff04ffff0133ff018080",
            "solution": "0xff64ffa0c363c01fea7794ea86c0801bf4ae8f210e3be0361dd0570b6ad185087367ce5380"
        }
    ]
}
```
### Farmers Steal Our Coins As Fees

The malicious farmer can also steal mojos by spending contribution coins and take our mojos as transaction fees!

```json
{
    "aggregated_signature": "0xc00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "coin_solutions": [
        {
            "coin": {
                "amount": 100,
                "parent_coin_info": "0x6ab2cf770c6a9a257fcd186c37b38b1aaace19e1e5385af6c32259995acbad7c",
                "puzzle_hash": "0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a"
            },
            "puzzle_reveal": "0x80",
            "solution": "0x80"
        },
        {
            "coin": {
                "amount": 100,
                "parent_coin_info": "0x61913992c00cc0c03229a97237168639a2cfc1c3f88572cb739954f2a310cf88",
                "puzzle_hash": "0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a"
            },
            "puzzle_reveal": "0x80",
            "solution": "0x80"
        },
        {
            "coin": {
                "amount": 100,
                "parent_coin_info": "0x6ae1ea8744f31d71c8ffd38a8b0d85b4749b31da23ebe176c23e4af2d0d10ea9",
                "puzzle_hash": "0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a"
            },
            "puzzle_reveal": "0x80",
            "solution": "0x80"
        }
    ]
}
```

We can verify that the contribution coins are spent on block **636507**.

```sh
❯ cdv rpc coinrecords --by puzhash 0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a -s 636449
[
    {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x61913992c00cc0c03229a97237168639a2cfc1c3f88572cb739954f2a310cf88",
            "puzzle_hash": "0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a"
        },
        "coinbase": false,
        "confirmed_block_index": 636464,
        "spent": true,
        "spent_block_index": 636507,
        "timestamp": 1632493591
    },
    {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x6ae1ea8744f31d71c8ffd38a8b0d85b4749b31da23ebe176c23e4af2d0d10ea9",
            "puzzle_hash": "0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a"
        },
        "coinbase": false,
        "confirmed_block_index": 636451,
        "spent": true,
        "spent_block_index": 636507,
        "timestamp": 1632493317
    },
    {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x6ab2cf770c6a9a257fcd186c37b38b1aaace19e1e5385af6c32259995acbad7c",
            "puzzle_hash": "0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a"
        },
        "coinbase": false,
        "confirmed_block_index": 636449,
        "spent": true,
        "spent_block_index": 636507,
        "timestamp": 1632493223
    }
]
```

So let's look at the block **636507**, and you will see that the farmer takes our **300** mojos as fees.

```sh
❯ cdv rpc blockrecords -i 636507
{
    ...
    "farmer_puzzle_hash": "0xb9528e87928844c2605d696d7b26d60e266c23af1c86bcde1b521ef7f130035e",
    "fees": 300,
    ...
    "header_hash": "0x2ed0caafde5e721396f0973d75ddb8b82ab3ef879312acc39eaf62e9cf9696c7",
    "height": 636507,
    ...
}
```

## Using ANNOUNCEMENT To Secure Contribution Coins

To prevent unintentionally contribution coin spending, we can use chialisp conditions. 

### New Contribution Coins

We add `ASSERT_PUZZLE_ANNOUNCEMENT` which forces the spend to be valid only if the announcement is created in the same block. The announcement makes sure that the contribution coin is spent together with a piggybank coin. 

The new piggybank coin has the **puzzle hash** (i.e., `0x5c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64`), and it annouces the message, **approved**.

Let's look at the new chialisp puzzle of the contribution coin:

```lisp
(mod ()

    (include condition_codes.clib)

    (defconstant PIGGYBANK_PUZZLE_HASH 0x5c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64)

    (list
        (list ASSERT_PUZZLE_ANNOUNCEMENT (sha256 PIGGYBANK_PUZZLE_HASH "approved"))
    )
)
```

Let's see if we can spend our new contribution coin (i.e., puzzle hash: `e6b571b019744c25e599c0f63593c4003b025c8f437c695b422b13d09bec9107`) after we add the `ASSERT_PUZZLE_ANNOUNCEMENT`. But first, we should deploy the new contribution coin to the blockchain.

```sh
❯ python3 -i ./piggybank_drivers.py
>>> CONTRIBUTION_MOD.get_tree_hash()
<bytes32: e6b571b019744c25e599c0f63593c4003b025c8f437c695b422b13d09bec9107>
>>> deploy_smart_coin(CONTRIBUTION_MOD, 100)
sending 100 to txch1u66hrvqew3xztevecrmrty7yqqasyhy0gd7xjk6z9vfapxlvjyrsmy9cns...
waiting until transaction 59ef79cde87d7f04823eaa81da3ee622decf280a6c3984b0acaa2eab93696469 is confirmed...
.........
# once it's done
❯ cdv rpc coinrecords --by puzhash e6b571b019744c25e599c0f63593c4003b025c8f437c695b422b13d09bec9107 -nd
{
    "7ff06f89a5fd1ce8822f78115afd68cb8e8036ff502e969ec904a3fcd19584d7": {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x2227900b2923b3c595cfe119604b75bdcf7bf4923bf7148cb53d73cd041c13db",
            "puzzle_hash": "0xe6b571b019744c25e599c0f63593c4003b025c8f437c695b422b13d09bec9107"
        },
        "coinbase": false,
        "confirmed_block_index": 659735,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1632930223
    }
}
```

Now, let's try to spend it.

```sh
❯ python3 -i ./piggybank_drivers.py
>>> cc = get_coin("7ff06f89a5fd1ce8822f78115afd68cb8e8036ff502e969ec904a3fcd19584d7")
>>> deposit_contrbution(cc)
{
    "aggregated_signature": "0xc00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "coin_solutions": [
        {
            "coin": {
                "amount": 100,
                "parent_coin_info": "0x2227900b2923b3c595cfe119604b75bdcf7bf4923bf7148cb53d73cd041c13db",
                "puzzle_hash": "0xe6b571b019744c25e599c0f63593c4003b025c8f437c695b422b13d09bec9107"
            },
            "puzzle_reveal": "0xff02ffff01ff04ffff04ff04ffff04ffff0bff06ffff0188617070726f76656480ff808080ff8080ffff04ffff01ff3fa05c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64ff018080",
            "solution": "0x80"
        }
    ]
}
Traceback (most recent call last):
  ...
ValueError: {'error': 'Failed to include transaction a4768dc4a8edbb3842b6bacca504509f3e7e318d1216b68457fbd84967ac6392, error ASSERT_ANNOUNCE_CONSUMED_FAILED', 'success': False}

>>> dc = get_coin("12c0709babe92736387cd4ab8b4082af3aab33422fcc9cd1092ba6f6f6b01b66")
>>> deposit_dummy(dc, cc, "0c799dadcbd2fbc719976d70f7d029e60923013e9818cab16f46865a6c748217")
{
    "aggregated_signature": "0xc00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "coin_solutions": [
        {
            "coin": {
                "amount": 100,
                "parent_coin_info": "0x2227900b2923b3c595cfe119604b75bdcf7bf4923bf7148cb53d73cd041c13db",
                "puzzle_hash": "0xe6b571b019744c25e599c0f63593c4003b025c8f437c695b422b13d09bec9107"
            },
            "puzzle_reveal": "0xff02ffff01ff04ffff04ff04ffff04ffff0bff06ffff0188617070726f76656480ff808080ff8080ffff04ffff01ff3fa05c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64ff018080",
            "solution": "0x80"
        },
        {
            "coin": {
                "amount": 0,
                "parent_coin_info": "0x9795b5b28882e26ee724e546c4c5ba28398f62eb62de9d6be1d4f75f7e29110e",
                "puzzle_hash": "0xb92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd"
            },
            "puzzle_reveal": "0xff02ffff01ff04ffff04ff02ffff04ff0bffff04ff05ff80808080ff8080ffff04ffff0133ff018080",
            "solution": "0xff64ffa00c799dadcbd2fbc719976d70f7d029e60923013e9818cab16f46865a6c74821780"
        }
    ]
}
Traceback (most recent call last):
  ...
ValueError: {'error': 'Failed to include transaction e0d9c652a97f33ab8d3ec03be7019d74b58ad0633f86222f73fea555ca2afadd, error ASSERT_ANNOUNCE_CONSUMED_FAILED', 'success': False}
```

Sweet! Both spends with and without dummy coin fail with the error, `ASSERT_ANNOUNCE_CONSUMED_FAILED`, and our contribution coin is still intact.


```sh
❯ cdv rpc coinrecords --by id 7ff06f89a5fd1ce8822f78115afd68cb8e8036ff502e969ec904a3fcd19584d7
[
    {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x2227900b2923b3c595cfe119604b75bdcf7bf4923bf7148cb53d73cd041c13db",
            "puzzle_hash": "0xe6b571b019744c25e599c0f63593c4003b025c8f437c695b422b13d09bec9107"
        },
        "coinbase": false,
        "confirmed_block_index": 659735,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1632930223
    }
]
```

### New Piggybank Coins

If we want to be able to spend our contribution coins (i.e., deposit to the piggybank), we will need to update [piggybank.clsp](https://github.com/kimsk/chia-piggybank/commit/3e6b22007a1826cd528409cb825637d2b170b87c#diff-1aac05a82431cbcd8a6462c03805dc01b56db6b624a0e505e25ed42de5df32e4) by adding `CREATE_PUZZLE_ANNOUNCEMENT` with the message, **approved**.

```lisp
...
  (defun-inline cash_out (CASH_OUT_PUZZLE_HASH new_amount my_puzzlehash)
    (list
      (list CREATE_COIN CASH_OUT_PUZZLE_HASH new_amount)
      (list CREATE_COIN my_puzzlehash 0)
      (list CREATE_PUZZLE_ANNOUNCEMENT "approved")
    )
  )

  (defun-inline recreate_self (new_amount my_puzzlehash)
    (list
      (list CREATE_COIN my_puzzlehash new_amount)
      (list CREATE_PUZZLE_ANNOUNCEMENT "approved")
    )
  )
...
```

The new piggybank coin's puzzle hash is `5c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64` which is the [hard-coded puzzle hash](https://github.com/kimsk/chia-piggybank/blob/3e6b22007a1826cd528409cb825637d2b170b87c/piggybank/contribution.clsp#L5) in our new contribution coin's puzzle. Let see if we can now spend the contribution coin now:

```sh
>>> pc = get_coin("c2e3b33f62338b45a5fddaaaa6883ad878574adee9efd3470c34204b72db7704")
>>> deposit_piggybank(pc, cc)
{
    "aggregated_signature": "0xc00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "coin_solutions": [
        {
            "coin": {
                "amount": 100,
                "parent_coin_info": "0x2227900b2923b3c595cfe119604b75bdcf7bf4923bf7148cb53d73cd041c13db",
                "puzzle_hash": "0xe6b571b019744c25e599c0f63593c4003b025c8f437c695b422b13d09bec9107"
            },
            "puzzle_reveal": "0xff02ffff01ff04ffff04ff04ffff04ffff0bff06ffff0188617070726f76656480ff808080ff8080ffff04ffff01ff3fa05c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64ff018080",
            "solution": "0x80"
        },
        {
            "coin": {
                "amount": 0,
                "parent_coin_info": "0x8ef80196c5a03cc1d0a728806e6dc770d974b47bfc67358f6463235cc5bcde8d",
                "puzzle_hash": "0x5c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64"
            },
            "puzzle_reveal": "0xff02ffff01ff02ffff03ffff15ff0bff0580ffff01ff02ffff03ffff15ff0bff0e80ffff01ff04ffff04ff0cffff04ff08ffff04ff0bff80808080ffff04ffff04ff0cffff04ff17ffff01ff80808080ffff04ffff04ff0affff01ff88617070726f7665648080ff80808080ffff01ff04ffff04ff0cffff04ff17ffff04ff0bff80808080ffff04ffff04ff0affff01ff88617070726f7665648080ff80808080ff0180ffff01ff088080ff0180ffff04ffff01ffffa0a6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e633ff3e8201f4ff018080",
            "solution": "0xff80ff64ffa05c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f6480"
        }
    ]
}
{
    "status": "SUCCESS",
    "success": true
}
```

The result looks good! We spend the contribution coin and deposit **100** mojos to the piggybank. Let's double check:

```sh
❯ cdv rpc coinrecords --by puzhash 5c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64
[
    {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0xc2e3b33f62338b45a5fddaaaa6883ad878574adee9efd3470c34204b72db7704",
            "puzzle_hash": "0x5c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64"
        },
        "coinbase": false,
        "confirmed_block_index": 659746,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1632930476
    },
    {
        "coin": {
            "amount": 0,
            "parent_coin_info": "0x8ef80196c5a03cc1d0a728806e6dc770d974b47bfc67358f6463235cc5bcde8d",
            "puzzle_hash": "0x5c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64"
        },
        "coinbase": false,
        "confirmed_block_index": 659576,
        "spent": true,
        "spent_block_index": 659746,
        "timestamp": 1632927634
    }
]
```

We see both spent piggybank with **zero** mojo and a new one with **100** mojos!

> If we want to see the real output from those spends above, we can use `cdv inspect spendbundles <spend bundle json file> -db` to see debugging information such as the created & asserted announcement hash.

```sh
❯ cdv inspect spendbundles ./spend_bundle_pc_cc.json -db
...
-------

spent coins
  (0x2227900b2923b3c595cfe119604b75bdcf7bf4923bf7148cb53d73cd041c13db 0xe6b571b019744c25e599c0f63593c4003b025c8f437c695b422b13d09bec9107 100)
      => spent coin id 7ff06f89a5fd1ce8822f78115afd68cb8e8036ff502e969ec904a3fcd19584d7
  (0x8ef80196c5a03cc1d0a728806e6dc770d974b47bfc67358f6463235cc5bcde8d 0x5c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64 ())
      => spent coin id c2e3b33f62338b45a5fddaaaa6883ad878574adee9efd3470c34204b72db7704

created coins
  (0xc2e3b33f62338b45a5fddaaaa6883ad878574adee9efd3470c34204b72db7704 0x5c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64 100)
      => created coin id 926273035e3760dbbf158f560a7dbc248c6683488baac4e04588156f42f8e6fa
created puzzle announcements
  ['0x5c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64', '0x617070726f766564'] =>
      6aede5fb98a81e0ea3c1955f16dc2df5889908d839d30e10d180d29a5e872b44


zero_coin_set = []

created  puzzle announcements = ['6aede5fb98a81e0ea3c1955f16dc2df5889908d839d30e10d180d29a5e872b44']

asserted puzzle announcements = ['6aede5fb98a81e0ea3c1955f16dc2df5889908d839d30e10d180d29a5e872b44']

symdiff of puzzle announcements = []


================================================================================
...
```

## Conclusions

This post shows us how bad actors can steal our coins and how we can prevent them by using `ANNOUCEMENT`. `ANNOUCEMENT` ensures that a piggybank and contribution coin(s) have to be spent together.

However, our coin is still not totally secure. Let's the other issue and how we can prevent it in the [next post](POST-5.md).

## Files

- [piggybank.clsp](https://github.com/kimsk/chia-piggybank/blob/3e6b22007a1826cd528409cb825637d2b170b87c/piggybank/piggybank.clsp)
- [contribution.clsp](https://github.com/kimsk/chia-piggybank/blob/3e6b22007a1826cd528409cb825637d2b170b87c/piggybank/contribution.clsp)
- [dummy_coin.clsp](https://github.com/kimsk/chia-piggybank/blob/3e6b22007a1826cd528409cb825637d2b170b87c/piggybank/dummy_coin.clsp)
- [piggybank_drivers.py](https://github.com/kimsk/chia-piggybank/blob/3e6b22007a1826cd528409cb825637d2b170b87c/piggybank/piggybank_drivers.py)
- [spend_bundle_cc.json](https://github.com/kimsk/chia-piggybank/blob/3e6b22007a1826cd528409cb825637d2b170b87c/spend_bundles/spend_bundle_cc.json)
- [spend_bundle_dc_cc.json](https://github.com/kimsk/chia-piggybank/blob/3e6b22007a1826cd528409cb825637d2b170b87c/spend_bundles/spend_bundle_dc_cc.json)
- [spend_bundle_pc_cc.json](https://github.com/kimsk/chia-piggybank/blob/3e6b22007a1826cd528409cb825637d2b170b87c/spend_bundles/spend_bundle_pc_cc.json)
- [spend_bundle_pc_ccs.json](https://github.com/kimsk/chia-piggybank/blob/3e6b22007a1826cd528409cb825637d2b170b87c/spend_bundles/spend_bundle_pc_ccs.json)


## References

- [chialsip.com | 8 - Security](https://chialisp.com/docs/security)
- [tutorial | 4 - Securing a Smart Coin](https://youtu.be/_SBGfMZhRd8)
- [High Level Tips 1 - Managing State, Coin Creation, Announcements](https://www.youtube.com/watch?v=lDXB4NlbQ-E)
- [High Level Tips 2 - Security, Checking Arguments & Signatures](https://www.youtube.com/watch?v=T4noZyNJkFA)
