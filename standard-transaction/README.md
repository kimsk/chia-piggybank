# The Standard Transaction

So far, all of the Chialisp puzzles we see from the previous posts have one thing in common; the puzzle itself creates the conditions. However, [the puzzle could also be provided the conditions as solution to output as well](https://chialisp.com/docs/coins_spends_and_wallets#generating-conditions-from-the-puzzle-vs-from-the-solution).

Here is the simplest example:

``` lisp
(mod conditions
    conditions
)
```

``` sh
❯ brun (run '(mod conditions conditions)') '((51 0xcafef00d 1000) (73 1000))'      
((51 0xcafef00d 1000) (73 1000))
```

## Delegated Puzzle

Better yet, Chialisp puzzle, treating code (as a 1st class citizen) like data, can be provided [a puzzle and solution to execute](https://chialisp.com/docs/coins_spends_and_wallets#example-pay-to-delegated-puzzle) and output the conditions! 

We call the provided puzzle that can create the ouput conditions, [delegated puzzle](https://chialisp.com/docs/standard_transaction#pay-to-delegated-puzzle-or-hidden-puzzle).

Here is the simplest example:

```lisp
(mod (delegated_puzzle solution)
    (a delegated_puzzle solution)
)
```

Let's pass the simplest puzzle above:

```sh
❯ run '(mod conditions conditions)'                                                
1

❯ brun (run '(mod (delegated_puzzle solution) (a delegated_puzzle solution))') '(1 ((51 0xcafef00d 1000) (73 1000)))'
((51 0xcafef00d 1000) (73 1000))
```

## AGG_SIG_ME

But as we know, the puzzle is not secure if there is no `AGG_SIG_ME` in the list of conditions. Also, we will need to have **public key** available too if we want to include `AGG_SIG_ME` condition.

Here is the version with `AGG_SIG_ME`:

[simple_pay_to_delegated.clsp](simple_pay_to_delegated.clsp)
```lisp
(mod (PUB_KEY delegated_puzzle solution)

    (include condition_codes.clib)

    (c
        (list AGG_SIG_ME PUB_KEY (sha256 "hello delegated puzzle"))
        (a delegated_puzzle solution)
    )
)
```

[simple_pay_to_delegated.py](simple_pay_to_delegated.py)
```python
...

MOD = load_clvm("simple_pay_to_delegated.clsp", package_or_requirement=__name__, search_paths=["../include"])

# create a smart coin and curry in alice's pk
amt = 1_000_000
alice_mod = MOD.curry(alice.pk())
alice_coin = asyncio.run(
    alice.launch_smart_coin(
        alice_mod,
        amt=amt
    )
)

# (delegated_puzzle solution)
solution = Program.to([
    1, # (mod conditions conditions)
    [
        [ConditionOpcode.CREATE_COIN, bob.puzzle_hash, amt],
        [ConditionOpcode.ASSERT_MY_AMOUNT, alice_coin.amount]
    ]
])

# create a spend bundle with alice's signature
spend = CoinSpend(
    alice_coin.as_coin(),
    alice_mod,
    solution 
)

message: bytes = std_hash(bytes("hello delegated puzzle", "utf-8"))
alice_sk: PrivateKey = alice.pk_to_sk(alice.pk())
sig: G2Element = AugSchemeMPL.sign(
    alice_sk,
    message
    + alice_coin.name()
    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA,
)

spend_bundle = SpendBundle([spend], sig)
```

Running the simulation:

```sh
❯ python3 ./simple_pay_to_delegated.py
alice balance:  2000000000000
alice smart coin:       {'amount': 1000000,
 'parent_coin_info': '0x8d011a3236082916e08a2214379a063b38a8c7c2ed7fb6a708acf824e1d9b310',
 'puzzle_hash': '0x1a54f0b830d632b8ccbbf8ce0202489ce9312aad6f407c1ddb21def66e763345'}

push spend bundle:
{'aggregated_signature': '0x8a1fe76f86f45975bad21b38ab759675300f04c02be911b572d66270e56d1c87ddb9255bbaeca646f72e97d94e1737d0169130ee2c9038a154fe15fdc6218f36e30deaf4a00914659156dc91f68e6ceae3cbdc9c9ee182e19b04f3f082d08c92',
 'coin_spends': [{'coin': {'amount': 1000000,
                           'parent_coin_info': '0x8d011a3236082916e08a2214379a063b38a8c7c2ed7fb6a708acf824e1d9b310',
                           'puzzle_hash': '0x1a54f0b830d632b8ccbbf8ce0202489ce9312aad6f407c1ddb21def66e763345'},
                  'puzzle_reveal': '0xff02ffff01ff02ffff01ff04ffff04ff02ffff04ff05ffff01ffa011e82913276355e092ff40373677de4a87461938fb975e02b0ffe08fb3d88ba9808080ffff02ff0bff178080ffff04ffff0132ff018080ffff04ffff01b0ac2f40f6cb161f872f61910bdacd811534e5b5753242553d9022906cdfa479e172b1eac8e1f38a3743b7897e58942442ff018080',
                  'solution': '0xff01ffffff33ffa05abb5d5568b4a7411dd97b3356cfedfac09b5fb35621a7fa29ab9b59dc905fb6ff830f424080ffff49ff830f4240808080'}]}

alice balance:  1999999000000
bob balance:    1000000
```

## Sign Delegated Puzzle Hash

The above example is not secure because the malicious actor can modify the delegated puzzle and solution. _We could fix this by signing the hash of the delegated puzzle, so we are certain that nobody changes the delegated puzzle_.

```lisp
(c
    (list AGG_SIG_ME PUB_KEY (sha256tree delegated_puzzle))
    (a delegated_puzzle solution)
)
```

```python
message: bytes = Program.to(1).get_tree_hash() # (mod conditions conditions)
alice_sk: PrivateKey = alice.pk_to_sk(alice.pk())
sig: G2Element = AugSchemeMPL.sign(
    alice_sk,
    message
    + alice_coin.name()
    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA,
)
```

The python code above shows how we pre-committed the delegated puzzle, `1` or `(mod conditions conditions)` without storing it inside the coin puzzle. We verify that the provided `delegated_puzzle` matches the expected puzzle by verifying the puzzle hash using `AGG_SIG_ME`.

## Hidden Puzzle

However, we want the ability to pre-commit to a puzzle without revealing other coins that have the same pre-committed hidden puzzle.

For example, if we want to pre-committed password-locked puzzle below to our coin puzzle:

```lisp
; hello is a password
(mod
    (password new_puzhash amount)
    (if (= (sha256 password) (q . 0x2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824))
            (list (list 51 new_puzhash amount))
            (x "wrong password")
    )
)
; puzzle hash is 0x5aa1f8e77872fa19b0227e752dee6bafa18b43d37996c4b2a5a845d8959baa2c
```

We can create a coin puzzle which will verify the delegated puzzle hash.

```lisp
; coin puzzle
(mod (PUB_KEY delegated_puzzle solution)

    (include condition_codes.clib)
    (include sha256tree.clib)

    (c
        (list AGG_SIG_ME PUB_KEY (sha256tree delegated_puzzle))
        (a delegated_puzzle solution)
    )
)
```

Let's run our puzzle:

```sh
# curry in PUB_KEY
❯ cdv clsp curry ./password-locked-coin.clsp -i ../include -a 0xcafef00d
(a (q 2 (q 4 (c 4 (c 5 (c (a 6 (c 2 (c 11 ()))) ()))) (a 11 23)) (c (q 50 2 (i (l 5) (q 11 (q . 2) (a 6 (c 2 (c 9 ()))) (a 6 (c 2 (c 13 ())))) (q 11 (q . 1) 5)) 1) 1)) (c (q . 0xcafef00d) 1))


# get coin's puzzle hash
❯ cdv clsp curry ./password-locked-coin.clsp -i ../include -a 0xcafef00d --treehash
139bfaabb5949487bbe9a73051d5dd44c75ccb99480ff0f02d58ff5ca1b10ef3

# wrong password
❯ brun '(a (q 2 (q 4 (c 4 (c 5 (c (a 6 (c 2 (c 11 ()))) ()))) (a 11 23)) (c (q 50 2 (i (l 5) (q 11 (q . 2) (a 6 (c 2 (c 9 ()))) (a 6 (c 2 (c 13 ())))) (q 11 (q . 1) 5)) 1) 1)) (c (q . 0xcafef00d) 1))' '((a (i (= (sha256 2) (q . 0x2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824)) (q 4 (c (q . 51) (c 5 (c 11 ()))) ()) (q 8 (q . \"wrong password\"))) 1) (\"hi\" 0xdeadbeef 100))'  
FAIL: clvm raise ("wrong password")

# successful spending
❯ brun '(a (q 2 (q 4 (c 4 (c 5 (c (a 6 (c 2 (c 11 ()))) ()))) (a 11 23)) (c (q 50 2 (i (l 5) (q 11 (q . 2) (a 6 (c 2 (c 9 ()))) (a 6 (c 2 (c 13 ())))) (q 11 (q . 1) 5)) 1) 1)) (c (q . 0xcafef00d) 1))' '((a (i (= (sha256 2) (q . 0x2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824)) (q 4 (c (q . 51) (c 5 (c 11 ()))) ()) (q 8 (q . \"wrong password\"))) 1) (\"hello\" 0xdeadbeef 100))'  
((50 0xcafef00d 0x5aa1f8e77872fa19b0227e752dee6bafa18b43d37996c4b2a5a845d8959baa2c) (51 0xdeadbeef 100))
```

The problem is once we spend one password-locked-coin puzzle, the `delegated_puzzle` is then revealed. Anyone will know what the delegated puzzle (and its puzzle hash) and solution is for any unspent coins with hash, `0x139bfaabb5949487bbe9a73051d5dd44c75ccb99480ff0f02d58ff5ca1b10ef3`.

We want an ability to pre-commit to a puzzle without revealing other coins that have the same pre-committed hidden puzzle.

### Synthetic Key

The solution is to generate a new public key from 
1. the hidden puzzle itself and
2. the public key that can sign for the delegated spend case.

`synthetic_offset == sha256(hidden_puzzle_hash + original_public_key)`

`synthentic_public_key == original_public_key + synthetic_offset_pubkey`

![Taproot Public Key Generation](https://www.chia.net/assets/blog/Taproot-Pub-Key-Generation.png)

We will modify our original coin puzzle to use `synthetic public key` and also verify that the hidden puzzle is correct. 

[password-locked-coin.clsp](password-locked-coin.clsp)
```lisp
(mod (SYNTHETIC_PK original_pk delegated_puzzle solution)

    (include condition_codes.clib)
    (include sha256tree.clib)

    (defun-inline is_hidden_puzzle_correct (SYNTHETIC_PK original_pk delegated_puzzle)
      (=
          SYNTHETIC_PK
          (point_add
              original_pk
              (pubkey_for_exp (sha256 original_pk (sha256tree delegated_puzzle)))
          )
      )
    )

    (if (is_hidden_puzzle_correct SYNTHETIC_PK original_pk delegated_puzzle)
        (c
            (list AGG_SIG_ME SYNTHETIC_PK (sha256tree delegated_puzzle))
            (a delegated_puzzle solution)
        )
        (x "wrong delegated puzzle")
    )
)
```

[synthetic-key-demo.py](synthetic-key-demo.py)
```python
# synthetic public key
synthetic_pk: G1Element = calculate_synthetic_public_key(
    alice.pk(),
    password_locked_delegated_hash
)

# synthetic private key
synthetic_sk: PrivateKey = calculate_synthetic_secret_key(
    alice.sk_,
    password_locked_delegated_hash
)

# (SYNTHETIC_PK original_pk delegated_puzzle solution)
# original_pk is alice's pk
# delegated_puzzle is password-locked delegated
# solution is ("hello" bob_puzz_hash amt)
# sending mojos to bob
password_locked_coin_solution = Program.to([
    alice.pk(),
    password_locked_delegated,
    ["hello", bob.puzzle_hash, amt]
])
```


## Pay To Delegated Puzzle or Hidden Puzzle

Chia team provides and recommmends utilizing a **standard transaction** with [Pay to "Delegated Puzzle" or "Hidden Puzzle"](https://chialisp.com/docs/standard_transaction#pay-to-delegated-puzzle-or-hidden-puzzle) for most vanilla transactions. Coins with the [puzzle](https://github.com/Chia-Network/chia-blockchain/blob/main/chia/wallet/puzzles/p2_delegated_puzzle_or_hidden_puzzle.clvm) can be unlocked by either signing a delegated puzzle and its solution with a **synthetic private key** OR by **revealing the hidden puzzle and the underlying original key**.

## Spend Standard Transaction

The cool thing about the standard transaction is that we can control how the standard transaction coin is spent by providing our own delegated puzzle and solutions.

Let's look at some scenarios that we can use the `p2_delegated_puzzle_or_hidden_puzzle`.

1. [Normal Spend](normal-spend.py)
    - `DEFAULT_HIDDEN_PUZZLE_HASH`
    - alice is the coin owner and wants to send coin to bob
    
1. [Approved Spend (2 of 2)](approved-spend.py)
    - `DEFAULT_HIDDEN_PUZZLE_HASH`
    - alice is the coin owner (i.e., coin's puzzle hash encoded to alice's wallet address & changes return to alice).
    - alice wants to send xch to charlie.
    - bob needs to **approve** the amount and recipient's address.

1. Multi-sig (m of m)
    - alice, bob, and charlie wants to contribute 1 XCH each (total of 3 XCH) and give to ellen.
    

1. Others
    - [spend_coin_sim.py](spend_coin_sim.py)
    > alice sends xch to bob.

    - [spend_coin_testnet10.py](spend_coin_testnet10.py)
    > send random coin on testnet10





```sh
❯ brun '(a (q 2 (q 2 (i 11 (q 2 (i (= 5 (point_add 11 (pubkey_for_exp (sha256 11 (a 6 (c 2 (c 23 ()))))))) (q 2 23 47) (q 8)) 1) (q 4 (c 4 (c 5 (c (a 6 (c 2 (c 23 ()))) ()))) (a 23 47))) 1) (c (q 50 2 (i (l 5) (q 11 (q . 2) (a 6 (c 2 (c 9 ()))) (a 6 (c 2 (c 13 ())))) (q 11 (q . 1) 5)) 1) 1)) (c (q . 0xb50b02adba343fff8bf3a94e92ed7df43743aedf0006b81a6c00ae573c0cce7d08216f60886fe84e4078a5209b0e5171) 1))' '(() (q (51 0x5abb5d5568b4a7411dd97b3356cfedfac09b5fb35621a7fa29ab9b59dc905fb6 0x0f4240) (51 0x4eb7420f8651b09124e1d40cdc49eeddacbaa0c25e6ae5a0a482fac8e3b5259f 0x0197741199c0)) ())'
((50 0xb50b02adba343fff8bf3a94e92ed7df43743aedf0006b81a6c00ae573c0cce7d08216f60886fe84e4078a5209b0e5171 0x1ec848ca82cf27fd8bcb2b796de6e8448576ac117c2cb4f4ba6f9d6c9c8d7a55) (51 0x5abb5d5568b4a7411dd97b3356cfedfac09b5fb35621a7fa29ab9b59dc905fb6 0x0f4240) (51 0x4eb7420f8651b09124e1d40cdc49eeddacbaa0c25e6ae5a0a482fac8e3b5259f 0x0197741199c0))
```

# References

- [Aggregated Signatures, Taproot, Graftroot, and Standard Transactions](https://www.chia.net/2021/05/27/Agrgregated-Sigs-Taproot-Graftroot.html)- [2 - Coins, Spends and Wallets | Chialisp.com](https://chialisp.com/docs/coins_spends_and_wallets/)
- [3 - Deeper into CLVM | Chialisp.com](https://chialisp.com/docs/deeper_into_clvm/)
- [6 - The Standard Transaction | Chialisp.com](https://chialisp.com/docs/standard_transaction/)
- [Signatures in Chia](https://aggsig.me/signatures.html)
- [chia.wallet.puzzles.p2_delegated_puzzle_or_hidden_puzzle](https://github.com/Chia-Network/chia-blockchain/blob/main/chia/wallet/puzzles/p2_delegated_puzzle_or_hidden_puzzle.py)
- [What is Taproot? Technology to Enhance Bitcoin’s Privacy](https://blockonomi.com/bitcoin-taproot/)
- [What is Bitcoin’s Graftroot? Complete Beginner’s Guide](https://blockonomi.com/bitcoin-graftroot/)
- [Multi-signature application examples](https://en.bitcoin.it/wiki/Multi-signature)
