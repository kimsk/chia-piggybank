# Writing (An Unsecure) Piggybank Coin
The piggybank smart coin acts like a piggybank which allows anyone to contribue money to the piggybank. Once piggybank reaches the target amount, it'd payout to the specified cash-out address/puzzle hash automatically. Once the cash-out happens, the new piggybank is created with zero amount.

> Since anyone can contribute and cash-out happens only when the amount reaches the goal, the good use case is something like crowd funding.

## Coin's state
The piggybank coin keeps the following information:

1. current amount & puzzle hash: these are kept automatically because every coin has to know its amount and puzzle hash. `coin_id` are basically the `sha256` hash of `parent_id`, `amount`, and `puzzlehash`.
2. target amount: the piggybank coin needs to decide if its new amount (`current + new amount`) meets the target.
3. cash-out address/puzzle hash: if its amount meets the target amount, new coin with the new amount is created and paid to the cash-out address.

To contribute more money (i.e., change the coin's amount), the existing coin has to be spent, and either the new piggybank coin with the new amount is created, or the new coin is created and paid to the cash-out address.

## Spend the coin
Everytime we spend the piggybank coin and the new piggybank coin is created, `parent_id` and `amount` will be different. The `parent_id` will be the `coin_id` of the spent piggybank coin while the `amount` will be the `amount` of the spent piggybank coin plus the `new_amount` or `0` if the cash-out happens.

## Puzzle's Arguments
```lisp
(
    my_amount
    new_amount
    my_puzzlehash
)
```

Although `amount` and `puzzle hash` are kept in the coin, we could not use coin's puzzle to get them. That's why we need to pass them as arguments.

> This means `puzzle` is a [pure function](https://en.wikipedia.org/wiki/Pure_function). Applying `solutions` to `puzzle` is deterministic because we will always get the same output (`conditions`) regardless of where it's run (e.g., locally using `brun` or remotely on full node) or what's the amount the smart coins hold.


> In this video, the `my_amount` is used to make sure it's less than `new_amount`. We don't need `my_amount` to create a new coin as to create a new coin we only need `new_amount` and `puzzle hash`, so we can remove `my_amount` from those inline functions.

## Puzzle's Constants
```lisp
(defconstant TARGET_AMOUNT 500)
(defconstant CASH_OUT_PUZZLE_HASH 0xcafef00d)
```

Since we want `TARGET_AMOUNT` and `CASH_OUT_PUZZLE_HASH` to be the same for every piggybank coin, they are set as constants in the puzzle.

## Cash-out Puzzle Hash
In Chia, the wallet address is the `bech32m` encoded puzzle hash. :exploding_head: Hence, we can get the `CASH_OUT_PUZZLE_HASH` by decoding the wallet address.

```sh
❯ chia wallet get_address -f 221573580
txch156jw6dev0pvpd7ujldumjm7hl96csyvs0a6whcvfeye3pca638nquar63h
```

I am using `testnet7` and the wallet address is `txch156jw6dev0pvpd7ujldumjm7hl96csyvs0a6whcvfeye3pca638nquar63h`. We can use `cdv` to decode it to get the puzzle hash.

```sh
❯ cdv decode txch156jw6dev0pvpd7ujldumjm7hl96csyvs0a6whcvfeye3pca638nquar63h
a6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6

# sanity check
❯ cdv encode a6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 --prefix txch
txch156jw6dev0pvpd7ujldumjm7hl96csyvs0a6whcvfeye3pca638nquar63h
```
Read [Chia Keys Architecture](https://github.com/Chia-Network/chia-blockchain/wiki/Chia-Keys-Architecture) to learn more.

I then change the `CASH_OUT_PUZZLE_HASH` to be my puzzle hash above (don't forget to prefix with `0x`).
```lisp
(defconstant CASH_OUT_PUZZLE_HASH 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6)
```

## Build the puzzle

First let's pull the `condition_codes` library and compile our `chialisp` puzzle using `cdv clsp`.

```sh
❯ cdv clsp retrieve condition_codes

❯ cdv clsp build ./piggybank/piggybank.clsp
Beginning compilation of piggybank.clsp...
...Compilation finished
```

After two steps above, we should see `clib` and `clsp.hex` files.
```sh
~/chia/chia-piggybank-tutorials
❯ ls include
───┬──────────────────────────────┬──────┬────────┬──────────────
 # │             name             │ type │  size  │   modified
───┼──────────────────────────────┼──────┼────────┼──────────────
 0 │ include/condition_codes.clib │ File │ 1.1 KB │ a minute ago
───┴──────────────────────────────┴──────┴────────┴──────────────


~/chia/chia-piggybank-tutorials
❯ ls piggybank
───┬──────────────────────────────┬──────┬───────┬────────────────
 # │             name             │ type │ size  │    modified
───┼──────────────────────────────┼──────┼───────┼────────────────
 0 │ piggybank/piggybank.clsp     │ File │ 774 B │ 2 minutes ago
 1 │ piggybank/piggybank.clsp.hex │ File │ 350 B │ 22 seconds ago
───┴──────────────────────────────┴──────┴───────┴────────────────
```

`clsp.hex` is the serialized version of the `clvm` code and we can get the `clvm` by using `cdv clsp disassemble`.

```sh
~/chia/chia-piggybank-tutorials
❯ bat piggybank/piggybank.clsp.hex
───────┬────────────────────────────────────────────────────────────────────────────────────────────────
       │ File: piggybank/piggybank.clsp.hex
───────┼────────────────────────────────────────────────────────────────────────────────────────────────
   1   │ ff02ffff01ff02ffff03ffff15ff0bff0580ffff01ff02ffff03ffff15ff0bff0e80ffff01ff04ffff04ff0affff04f
       │ f04ffff04ff0bff80808080ffff04ffff04ff0affff04ff17ffff01ff80808080ff808080ffff01ff04ffff04ff0aff
       │ ff04ff17ffff04ff0bff80808080ff808080ff0180ffff01ff088080ff0180ffff04ffff01ffa0a6a4ed372c785816f
       │ b92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6ff338201f4ff018080
───────┴────────────────────────────────────────────────────────────────────────────────────────────────

~/chia/chia-piggybank-tutorials
❯ cdv clsp disassemble ./piggybank/piggybank.clsp.hex | bat -l lisp
───────┬────────────────────────────────────────────────────────────────────────────────────────────────
       │ STDIN
───────┼────────────────────────────────────────────────────────────────────────────────────────────────
   1   │ (a (q 2 (i (> 11 5) (q 2 (i (> 11 14) (q 4 (c 10 (c 4 (c 11 ()))) (c (c 10 (c 23 (q ()))) ()))
       │ (q 4 (c 10 (c 23 (c 11 ()))) ())) 1) (q 8)) 1) (c (q 0xa6a4ed372c785816fb92fb79b96fd7f975881190
       │ 7f74ebe189c93310e3ba89e6 51 . 500) 1))
───────┴────────────────────────────────────────────────────────────────────────────────────────────────

```

## Test locally

### The Sad Path
If the `new_amount` is less than the current amount, the puzzle should raise the exception.
```sh
❯ brun (cdv clsp disassemble piggybank/piggybank.clsp.hex) '(100 0 0xcafef00d)'
FAIL: clvm raise ()
```

### The Happy Paths
Now, let's test normal piggybank contribution. We should see a new piggybank coin created with the new amount.
```sh
❯ brun (cdv clsp disassemble piggybank/piggybank.clsp.hex) '(0 100 0xcafef00d)'
((51 0xcafef00d 100))
```
> `(defconstant CREATE_COIN 51)` is defined in `include/condition_codes.clib`

Finally, let's test piggybank cash out. We should see two coins created. The first one is the cash out coin which paid 501 mojos to the puzzle hash defined above. And the second one is the new piggybank coin with **0** mojo.
```sh
❯ brun (cdv clsp disassemble piggybank/piggybank.clsp.hex) '(100 501 0xcafef00d)'
((51 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 501) (51 0xcafef00d ()))
```
We should notice that the puzzle hash in the solution can be anything and this is a security concern. Let's ignore that for now. The concern will be addressed in the later posts.

## Deploy the Smart Coin
We have been working locally so far. Next step is to deploy the smart coin to the blockchain. What we need to do is to send **0** mojo coin with the hash of our final puzzle below.

```lisp
(mod (
        my_amount
        new_amount
        my_puzzlehash
     )

  (include condition_codes.clib)

  (defconstant TARGET_AMOUNT 500)
  (defconstant CASH_OUT_PUZZLE_HASH 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6)

  (defun-inline cash_out (CASH_OUT_PUZZLE_HASH new_amount my_puzzlehash)
    (list
      (list CREATE_COIN CASH_OUT_PUZZLE_HASH new_amount)
      (list CREATE_COIN my_puzzlehash 0)
    )
  )

  (defun-inline recreate_self (new_amount my_puzzlehash)
    (list
      (list CREATE_COIN my_puzzlehash new_amount)
    )
  )

  ; main
  (if (> new_amount my_amount)
    (if (> new_amount TARGET_AMOUNT)
      (cash_out CASH_OUT_PUZZLE_HASH new_amount my_puzzlehash)
      (recreate_self new_amount my_puzzlehash)
    )
    (x)
  )
)
```

### Get the puzzle hash (i.e., treehash)

Again, we can use `cdv` to get the `treehash` and encode it to a received address.
```sh
❯ cdv clsp treehash ./piggybank/piggybank.clsp.hex
c23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8

❯ cdv encode (cdv clsp treehash ./piggybank/piggybank.clsp.hex) --prefix txch
txch1cg6n9h0mp4ux2n8h86dpuk6p0lrucygdgr9cczqe34s9wpjwkluqaq07sn
```

### Deploy

To deploy the smart coin, it's just sending **0** mojo to the address above.
```sh
chia wallet send -a 0 -t txch1cg6n9h0mp4ux2n8h86dpuk6p0lrucygdgr9cczqe34s9wpjwkluqaq07sn --override -f 3919172776

Submitting transaction...
Transaction submitted to nodes: [('cdd006a2b13679459a3cb68952c9ad46ebf467c79971d922105e88a4a8b8ff0b', 1, None)]
Do chia wallet get_transaction -f 3919172776 -tx 0x2aa8cc8889192c201588d0eb56fd67dd1d919f6d096ceee3e3dfb9d68544b70b to get status
```

> For some reason, I couldn't use the same key to deploy the piggybank coin, so I have to use different wallet key (fingerprint: 3919172776) instead.

The transaction should be confirmed shortly.
```sh
❯ chia wallet get_transaction -f 3919172776 -tx 0x2aa8cc8889192c201588d0eb56fd67dd1d919f6d096ceee3e3dfb9d68544b70b
Transaction 2aa8cc8889192c201588d0eb56fd67dd1d919f6d096ceee3e3dfb9d68544b70b
Status: Confirmed
Amount: 0 txch
To address: txch1cg6n9h0mp4ux2n8h86dpuk6p0lrucygdgr9cczqe34s9wpjwkluqaq07sn
Created at: 2021-08-31 22:10:47
```

After the transaction is confirmed, we can get `coin_records` by the puzzle hash, `0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8`.

```sh
❯ cdv rpc coinrecords --by puzhash 0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8
[{'coin': {'amount': 0,
           'parent_coin_info': '0xd84fbea32e0cfecbdc447de9ecb3ee8a9612ac8a5153a6f4335b174281a7d8bd',
           'puzzle_hash': '0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8'},
  'coinbase': False,
  'confirmed_block_index': 527000,
  'spent': False,
  'spent_block_index': 0,
  'timestamp': 1630422691}]
```

## Conclusion

That's it. We now have our (unsecure) piggybank coin on the blockchain! Next part, we will try to contribute and cash out the piggybank coin.

## Files

- [piggybank.clsp](https://github.com/kimsk/chia-piggybank/blob/d32c30d208073ded0146ea195d818e6d196b556a/piggybank/piggybank.clsp)

## References
- [tutorial | 2 - Start Writing Your First Smart Coin](https://youtu.be/v1o7fRHGPpM)
- [tutorial | 3 - Finish Writing Your First Smart Coin](https://www.youtube.com/watch?v=q1ZsTWRKd8A)
