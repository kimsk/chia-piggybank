# Securing Piggybank Coin (ANNOUCEMENT)

> [Money ain’t got no owners, just spenders](https://www.youtube.com/watch?v=PT2I1T87nwQ&t=133s) - Omar Little | The Wire


There is no concept of coin ownership as the wallet address is actually a [bech32m decoded puzzle hash](https://www.chiaexplorer.com/tools/address-puzzlehash-converter). So our puzzle has to be able to prevent the coin to be spent unintentionally. We have been coding our smart coins in chialisp and the driver code in python to make it easier to deploy and spend those coins. However, there is nothing to prevent other people to [spend](https://chialisp.com/docs/coins_spends_and_wallets#spends) our coins. 


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
### Steal By A Farmer

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


## References

- [chialsip.com | 8 - Security](https://chialisp.com/docs/security)
- [tutorial | 4 - Securing a Smart Coin](https://youtu.be/_SBGfMZhRd8)
- [High Level Tips 1 - Managing State, Coin Creation, Announcements](https://www.youtube.com/watch?v=lDXB4NlbQ-E)
- [High Level Tips 2 - Security, Checking Arguments & Signatures](https://www.youtube.com/watch?v=T4noZyNJkFA)
