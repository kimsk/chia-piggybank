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

Better yet, Chialisp puzzle, treating code (as a 1st class citizen) like data, can be provided [a puzzle and solution to execut](https://chialisp.com/docs/coins_spends_and_wallets#example-pay-to-delegated-puzzle) and output the conditions! 

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
