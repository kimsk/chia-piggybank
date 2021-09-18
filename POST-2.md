# Contribute and Cash Out A Piggybank Coin

Now we have the piggybank coin with zero amount. :mechanical_arm: How do we add money (contribute) to the piggybank?

```sh
❯ cdv rpc coinrecords --by puzhash 0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8
[{'coin': {'amount': 0,
           'parent_coin_info': '0xd84fbea32e0cfecbdc447de9ecb3ee8a9612ac8a5153a6f4335b174281a7d8bd',
           'puzzle_hash': '0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8'},
 ...
}
```

## Wrong Way To Contribute To The Piggybank Coin

We may tempt to use `chia wallet send` to send money to the same address again.

Let's try to send **100** mojos to the same address.
```sh
❯ chia wallet send -a 0.000000000100 -t txch1cg6n9h0mp4ux2n8h86dpuk6p0lrucygdgr9cczqe34s9wpjwkluqaq07sn -f 3919172776
Submitting transaction...
Transaction submitted to nodes: [('cdd006a2b13679459a3cb68952c9ad46ebf467c79971d922105e88a4a8b8ff0b', 1, None)]
Do chia wallet get_transaction -f 3919172776 -tx 0x1bb814c1cb48ed0fe0d7181679d99ba126ae197059123374467a00fb37de50a3 to get status
```

After the transaction is confirmed, let's try to get the coin records again.

```sh
❯ cdv rpc coinrecords --by puzhash 0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8
[{'coin': {'amount': 100,
           'parent_coin_info': '0x85212255f7a1fe92470601dc38e4b0178e583263ad80bddfa56e54464fdbc307',
           'puzzle_hash': '0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8'},
  ...
  'spent': False,...},
 {'coin': {'amount': 0,
           'parent_coin_info': '0xd84fbea32e0cfecbdc447de9ecb3ee8a9612ac8a5153a6f4335b174281a7d8bd',
           'puzzle_hash': '0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8'},
  ...
  'spent': False,...}]
```

Now we have **two** piggybank coins with zero and **100** mojos. **What we just did was creating another piggybank coin instead!** :facepalm:

What we really want to do is to **spend** the original piggybank coin by running the puzzle and have the new piggybank coin with the new amount created.

To contribute to the piggybank coin, we have to spend other coin(s) called **contribute coin(s)** together with the current piggybank coin in the same spend bundle. The new piggybank coin will have all the amount of all coins in the spend bundle.

## Contribution Coin

Because we just want to **burn** the contribution coin, the puzzle can be just an empty puzzle, `()`.

```sh
❯ cdv clsp build ./piggybank/contribution.clsp
Beginning compilation of contribution.clsp...
...Compilation finished

❯ cdv clsp treehash ./piggybank/contribution.clsp.hex
4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a

❯ cdv encode (cdv clsp treehash ./piggybank/contribution.clsp.hex) --prefix txch
txch1f063yte5g42v2w7796ace54hu0gkqzkkx8pctfwhen3rcau9gkdqpsnmae
```

Now we have the address, we can now deploy the contribution coin with any amount.

```sh
❯ chia wallet send -a 0.000000000100 -t txch1f063yte5g42v2w7796ace54hu0gkqzkkx8pctfwhen3rcau9gkdqpsnmae -f 3919172776

Submitting transaction...
Transaction submitted to nodes: [('cdd006a2b13679459a3cb68952c9ad46ebf467c79971d922105e88a4a8b8ff0b', 1, None)]
Do chia wallet get_transaction -f 3919172776 -tx 0x5786b6f6b4370241ee4e31d833f74bd8c71730ea729bab266dfd2ae88fe61a7a to get status

❯ cdv rpc coinrecords --by puzhash 0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a
[{'coin': {'amount': 100,
           'parent_coin_info': '0x1eb5f487ba4ddc4087a0e14214eb27c391ed133b5e47404b54f89437348340dc',
           'puzzle_hash': '0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a'},
  ...
  'spent': False,...}]
```

Cool, we have **100** mojos in the contribution coin that we can spend to contribute to the piggybank coin!

## Creating A Spend Bundle

When we do `chia wallet send`, we actually ask our [Chia wallet](https://chialisp.com/docs/coins_spends_and_wallets#wallets) to spend the coin that has a **standard send puzzle** that will verify that the spender is the coin owner and create a new **standard coin** that can be spent by the receiver (i.e., the new owner).

> [Kickoff Talk: "Why Chialisp"](https://www.youtube.com/watch?v=O0iae_-zXcs&t=2819s) explains the **standard send puzzle**, just in case anyone wants to learn more.

To contribute to the piggybank coin, we will create a spend bundle with two coins, the zero amount piggybank coin and the hundred mojos contribution coin.

### Piggybank Coin
```json
{
    "amount": 0,
    "parent_coin_info": "d84fbea32e0cfecbdc447de9ecb3ee8a9612ac8a5153a6f4335b174281a7d8bd",
    "puzzle_hash": "c23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8"
}
```

### Contribution Coin
```json
{
    "amount": 100,
    "parent_coin_info": "1eb5f487ba4ddc4087a0e14214eb27c391ed133b5e47404b54f89437348340dc",
    "puzzle_hash": "4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a"
}
```

To [spend a coin](https://chialisp.com/docs/coins_spends_and_wallets#spends), we also need to provide the full source of the coin's puzzle or `puzzle reveal` and `solution` to the puzzle. 

Lastly, we will need to provide `aggregated signature` for the spend bundle. In this case, we don't output any condition that will assert the signature (more on that later in the security post), we can just use an empty signature below:

`c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000`

We can get the `puzzle reveal` from the `clsp.hex` file. And the `solution` via `opc` command.

```sh
❯ bat piggybank/piggybank.clsp.hex
───────┬────────────────────────────────────────────────────────────────────────────────────────────────
       │ File: piggybank/piggybank.clsp.hex
───────┼────────────────────────────────────────────────────────────────────────────────────────────────
   1   │ ff02ffff01ff02ffff03ffff15ff0bff0580ffff01ff02ffff03ffff15ff0bff0e80ffff01ff04ffff04ff0affff04f
       │ f04ffff04ff0bff80808080ffff04ffff04ff0affff04ff17ffff01ff80808080ff808080ffff01ff04ffff04ff0aff
       │ ff04ff17ffff04ff0bff80808080ff808080ff0180ffff01ff088080ff0180ffff04ffff01ffa0a6a4ed372c785816f
       │ b92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6ff338201f4ff018080
───────┴────────────────────────────────────────────────────────────────────────────────────────────────

# (my_amount new_amount my_puzzlehash)
❯ opc '(0 100 0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8)'
ff80ff64ffa0c23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f880

❯ bat piggybank/contribution.clsp.hex
───────┬────────────────────────────────────────────────────────────────────────────────────────────────
       │ File: piggybank/contribution.clsp.hex
───────┼────────────────────────────────────────────────────────────────────────────────────────────────
   1   │ 80
───────┴────────────────────────────────────────────────────────────────────────────────────────────────

❯ opc '()'
80
```

Here is the full spend bundle:

```json
{
  "coin_spends": [
    {
      "coin": {
        "amount": 0,
        "parent_coin_info": "d84fbea32e0cfecbdc447de9ecb3ee8a9612ac8a5153a6f4335b174281a7d8bd",
        "puzzle_hash": "c23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8"
      },
      "puzzle_reveal": "ff02ffff01ff02ffff03ffff15ff0bff0580ffff01ff02ffff03ffff15ff0bff0e80ffff01ff04ffff04ff0affff04ff04ffff04ff0bff80808080ffff04ffff04ff0affff04ff17ffff01ff80808080ff808080ffff01ff04ffff04ff0affff04ff17ffff04ff0bff80808080ff808080ff0180ffff01ff088080ff0180ffff04ffff01ffa0a6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6ff338201f4ff018080",
      "solution": "ff80ff64ffa0c23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f880"
    },
    {
      "coin": {
        "amount": 100,
        "parent_coin_info": "1eb5f487ba4ddc4087a0e14214eb27c391ed133b5e47404b54f89437348340dc",
        "puzzle_hash": "4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a"
      },
      "puzzle_reveal": "80",
      "solution": "80"
    }
  ],
  "aggregated_signature": "c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
}
```

Before we push the spend bundle, we can use `cdv inspect` to test first.
```sh
❯ cdv inspect spendbundles ./spend_bundle-100.json -db
...

Debugging Information
---------------------
================================================================================
consuming coin (0xd84fbea32e0cfecbdc447de9ecb3ee8a9612ac8a5153a6f4335b174281a7d8bd 0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8 ())
  with id d0575e34fdfc65138cd49b37f6ae7f76abf991c3fa1954ed28f4980be1d3c0a6


brun -y main.sym '(a (q 2 (i (> 11 5) (q 2 (i (> 11 14) (q 4 (c 10 (c 4 (c 11 ()))) (c (c 10 (c 23 (q ()))) ())) (q 4 (c 10 (c 23 (c 11 ()))) ())) 1) (q 8)) 1) (c (q 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 51 . 500) 1))' '(() 100 0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8)'

((CREATE_COIN 0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8 100))

...

aggregated signature check pass: True
pks: []
msgs: []
  msg_data: []
  coin_ids: []
  add_data: []
signature: c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
None
```

We don't see any error, so let's spend it! We push the spend bundle to the blockchain by using `cdv rpc pushtx`

```sh
{'status': 'SUCCESS', 'success': True}
```

We should now see a new **100** mojo coin has been created on the block `527384`. And both **0** mojo piggybank coin and **contribution coin** have been spent on the same block, `527348`.
```sh
❯ cdv rpc coinrecords --by puzhash 0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8

[...
 {'coin': {'amount': 0,
           'parent_coin_info': '0xd84fbea32e0cfecbdc447de9ecb3ee8a9612ac8a5153a6f4335b174281a7d8bd',
           'puzzle_hash': '0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8'},
  ...
  'confirmed_block_index': 527000,
  'spent': True,
  'spent_block_index': 527384,
  'timestamp': 1630422691},
 {'coin': {'amount': 100,
           'parent_coin_info': '0xd0575e34fdfc65138cd49b37f6ae7f76abf991c3fa1954ed28f4980be1d3c0a6',
           'puzzle_hash': '0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8'},
  ...
  'confirmed_block_index': 527384,
  'spent': False,
  'spent_block_index': 0,
  'timestamp': 1630429009}]

❯ cdv rpc coinrecords --by puzhash 0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a
[{'coin': {'amount': 100,
           'parent_coin_info': '0x1eb5f487ba4ddc4087a0e14214eb27c391ed133b5e47404b54f89437348340dc',
           'puzzle_hash': '0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a'},
  'coinbase': False,
  'confirmed_block_index': 527222,
  'spent': True,
  'spent_block_index': 527384,
  'timestamp': 1630426132}]
```
## Piggybank Cash Out

Let's create more contribution coins and try to contribute until the we reach the target amount and cash-out.

```sh
❯ chia wallet send -a 0.000000000200 -t txch1f063yte5g42v2w7796ace54hu0gkqzkkx8pctfwhen3rcau9gkdqpsnmae -f 3919172776

❯ chia wallet send -a 0.000000000300 -t txch1f063yte5g42v2w7796ace54hu0gkqzkkx8pctfwhen3rcau9gkdqpsnmae -f 3919172776
```

> You might need to wait until the first transaction is confirmed before sending money again otherwise you will get `"Can't send more than 0 in a single transaction"` exception.

Wait a bit, and we should have our unspent **300** mojo and **200** mojo coins. Please note additional `-ou` flag to get only unspent coins.

```sh
❯ cdv rpc coinrecords -ou --by puzhash 0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a
[{'coin': {'amount': 300,
           'parent_coin_info': '0x854a5ab343621c37a3ee558f240c97b6aab65c8c1ac3ae98e3361da96be863e1',
           'puzzle_hash': '0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a'},
  'coinbase': False,
  'confirmed_block_index': 529551,
  'spent': False,
  'spent_block_index': 0,
  'timestamp': 1630468839},
 {'coin': {'amount': 200,
           'parent_coin_info': '0xc4c4dba448a3fee231287dde3fc25fa0c0a58e1e5c911806e079606db6cf8787',
           'puzzle_hash': '0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a'},
  'coinbase': False,
  'confirmed_block_index': 529594,
  'spent': False,
  'spent_block_index': 0,
  'timestamp': 1630469816}]
```
#### Contribute More Coins
Now let's spend **200** mojo coin and check the unspent piggybank coin.

> As you can see, the spend bundles have to be updated with different coin infos (i.e., `amount` and `parent_coin_info`, and `solution`) each time. And since our current puzzle has no `assertion`, wrong `solution` can cause wrong result. This can be very cumbersome and error-prone, so that's why we should have `driver code` doing this instead.

```sh
❯ cdv rpc coinrecords --by puzhash 0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8 -ou
[
 {'coin': {'amount': 300,
           'parent_coin_info': '0x95ece3272399a541e04641ed17453407b4588ba567e7a7b40add461e76493f08',
           'puzzle_hash': '0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8'},
  'coinbase': False,
  'confirmed_block_index': 529618,
  'spent': False,
  'spent_block_index': 0,
  'timestamp': 1630470400}]
```

Finally, we will spend **300** mojos and the cash out event should happen as we set the `TARGET_AMOUNT` to **500** mojos.

```sh
❯ cdv rpc pushtx ./spend_bundle-300.json
{'status': 'SUCCESS', 'success': True}
```

> We could also spend two or more contribution coins in one spend bundle. We just need to make sure we provide the correct solution (e.g., `new_amount = my_amount + SUM(contribution coins)`)

#### Check Piggybank Coins

We should see the following coins:

1. The original **0** mojo piggybank coin which was spent when we contribute 100 mojos.
2. The spent **100** mojo piggybank coin which was spent when we contribute 200 mojos.
3. The spent **300** mojo piggybank coin which was spent when we contribute 300 mojos and cash out.
4. A fresh unspent **0** mojo piggybank coin created when cash-out happens.

```sh
❯ cdv rpc coinrecords --by puzhash 0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8
[
    {'coin': {'amount': 0,
           'parent_coin_info': '0xd84fbea32e0cfecbdc447de9ecb3ee8a9612ac8a5153a6f4335b174281a7d8bd',
           'puzzle_hash': '0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8'},
  'coinbase': False,
  'confirmed_block_index': 527000,
  'spent': True,
  'spent_block_index': 527384,
  'timestamp': 1630422691},
    {'coin': {'amount': 100,
           'parent_coin_info': '0x54ed9b18c99406600fda49327fb32aee29d5674391411603a0cfeff684d92686',
           'puzzle_hash': '0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8'},
  'coinbase': False,
  'confirmed_block_index': 529577,
  'spent': True,
  'spent_block_index': 529618,
  'timestamp': 1630469472},
    {'coin': {'amount': 300,
           'parent_coin_info': '0x95ece3272399a541e04641ed17453407b4588ba567e7a7b40add461e76493f08',
           'puzzle_hash': '0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8'},
  'coinbase': False,
  'confirmed_block_index': 529618,
  'spent': True,
  'spent_block_index': 529661,
  'timestamp': 1630470400},
    {'coin': {'amount': 0,
           'parent_coin_info': '0x41c8dc381ecd3b3703b3f78de6cd4b9e6dcc9fa0eac2e7b083f039ac293956df',
           'puzzle_hash': '0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8'},
  'coinbase': False,
  'confirmed_block_index': 529661,
  'spent': False,
  'spent_block_index': 0,
  'timestamp': 1630471546}]
```

#### Check Contribution Coins

We should see three spent contribution coins with 100, 200, and 300 mojos amount.

```sh
❯ cdv rpc coinrecords --by puzhash 0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a
[{'coin': {'amount': 100,
           'parent_coin_info': '0x1eb5f487ba4ddc4087a0e14214eb27c391ed133b5e47404b54f89437348340dc',
           'puzzle_hash': '0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a'},
  'coinbase': False,
  'confirmed_block_index': 527222,
  'spent': True,
  'spent_block_index': 527384,
  'timestamp': 1630426132},
   {'coin': {'amount': 200,
           'parent_coin_info': '0xc4c4dba448a3fee231287dde3fc25fa0c0a58e1e5c911806e079606db6cf8787',
           'puzzle_hash': '0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a'},
  'coinbase': False,
  'confirmed_block_index': 529594,
  'spent': True,
  'spent_block_index': 529618,
  'timestamp': 1630469816},
    {'coin': {'amount': 300,
           'parent_coin_info': '0x854a5ab343621c37a3ee558f240c97b6aab65c8c1ac3ae98e3361da96be863e1',
           'puzzle_hash': '0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a'},
  'coinbase': False,
  'confirmed_block_index': 529551,
  'spent': True,
  'spent_block_index': 529661,
  'timestamp': 1630468839},
]
```

#### Check Cash Out Coin

From [Writing An (Unsecured) Piggybank Coin](PART-1.md), our `CASH_OUT_PUZZLE_HASH` is `0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6`, so we can check if we have **600** mojo coin.

```sh
❯ cdv rpc coinrecords --by puzhash 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6
[{'coin': {'amount': 600,
           'parent_coin_info': '0x41c8dc381ecd3b3703b3f78de6cd4b9e6dcc9fa0eac2e7b083f039ac293956df',
           'puzzle_hash': '0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6'},
  'coinbase': False,
  'confirmed_block_index': 529661,
  'spent': False,
  'spent_block_index': 0,
  'timestamp': 1630471546}]
```

If this is our wallet, we can check our wallet directly as well. :satisfied:
```sh
❯ chia wallet show -f 221573580
Wallet height: 529718
Sync status: Synced
Balances, fingerprint: 221573580
Wallet ID 1 type STANDARD_WALLET Chia Wallet
   -Total Balance: 6e-10 txch (600 mojo)
   -Pending Total Balance: 6e-10 txch (600 mojo)
   -Spendable: 6e-10 txch (600 mojo)

❯ curl --insecure --cert ~/.chia/testnet7/config/ssl/full_node/private_full_node.crt --key ~/.chia/testnet7/config/ssl/full_node/private_full_node.key -H "Content-Type: application/json" -X POST https://localhost:9256/get_wallet_balance -d '{"wallet_id": 1}' -s | jq
{
  "success": true,
  "wallet_balance": {
    "confirmed_wallet_balance": 600,
    "max_send_amount": 600,
    "pending_change": 0,
    "pending_coin_removal_count": 0,
    "spendable_balance": 600,
    "unconfirmed_wallet_balance": 600,
    "unspent_coin_count": 1,
    "wallet_id": 1
  }
}
```

## Conclusion

Now we know how to deploy a smart coin and spend them. Messing with a spend bundle file directly is very inconvenient, but it's good to know how things work. Next post, we will do the samething but with the driver code.

> Please note that our piggybank and contribution coins are not secured at all. We will strenghten it up later when walkthrough [4 - Securing a Smart Coin](https://youtu.be/_SBGfMZhRd8) tutorial.

### References

[8 - Deploying a Smart Coin to the Blockchain](https://www.youtube.com/watch?v=Y_p9qF2XLks)

[9 - Spending Your Smart Coin](https://www.youtube.com/watch?v=KGC5zACBjkY)
