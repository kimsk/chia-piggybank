# Securing Piggybank Coin (ASSERT_MY_*)

In the [last post](POST-4.md), we are able to guarantee that our contribution coins have to be spent together with our designated piggybank coin by aseerting puzzle annoucement.

However, the existing piggybank coin still has issues allowing bad actors to steal our mojos. Let's look at those issues together:

## Problem With Piggybank Solution

Let's look at the `recreate_self` function again:

```lisp
(mod (
        my_amount
        new_amount
        my_puzzlehash
     )
  ...
  (defun-inline recreate_self (new_amount my_puzzlehash)
    (list
      (list CREATE_COIN my_puzzlehash new_amount)
      (list CREATE_PUZZLE_ANNOUNCEMENT "approved")
    )
  )
  ...
)
```

### `my_puzzlehash`

We can see that, `my_puzzlehash` which is a part of the solution to the puzzle can be anything. Any bad actors can create a spend bundle with their wallet's puzzle hash and steal our mojos by providing their own puzzle hash.


To help us working on this issue, we add the code to allow puzzle hash to be set manually (instead of using piggybank coin puzzle hash).

```python
def deposit_to_puzzle_hash(pc: Coin, cc: Coin, puzzle_hash):
    piggybank_spend = CoinSpend(
        pc,
        PIGGYBANK_MOD,
        Program.to([pc.amount, (pc.amount + cc.amount), puzzle_hash])

    )
    contribution_spend = CoinSpend(cc, CONTRIBUTION_MOD, solution_for_contribution())

    spend(
        [piggybank_spend, contribution_spend],
        signature = G2Element()
    )
```

Let's list the existing piggybank coin and contribution coins:

```sh
❯ cdv rpc coinrecords --by puzhash 5c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64 -ou -nd
{
    "4ebcd582063a4a3a3ecd3dc5ae6cab14cc6e448ad5e06e26b258e065d571c265": {
        "coin": {
            "amount": 0,
            "parent_coin_info": "0x926273035e3760dbbf158f560a7dbc248c6683488baac4e04588156f42f8e6fa",
            "puzzle_hash": "0x5c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64"
        },
        "coinbase": false,
        "confirmed_block_index": 659908,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1632932684
    }
}

❯ cdv rpc coinrecords --by puzhash e6b571b019744c25e599c0f63593c4003b025c8f437c695b422b13d09bec9107 -ou -nd
{
    "1dcdaa3ae3ce5488ff40cc95362ddb8a15d859cbc1ec68e3aee7dd4f4c1adc6f": {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x69b093ab7438df7bfee13e220cc54ddfa92d059c21da1c4ff9ddf9ea8f6e6958",
            "puzzle_hash": "0xe6b571b019744c25e599c0f63593c4003b025c8f437c695b422b13d09bec9107"
        },
        "coinbase": false,
        "confirmed_block_index": 667979,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1633080337
    },...
}
```

We will spend two coins above with the dummy coin's puzzle hash:

```sh
❯ python3 -i ./piggybank_drivers.py
>>> pc = get_coin("4ebcd582063a4a3a3ecd3dc5ae6cab14cc6e448ad5e06e26b258e065d571c265")
>>> cc = get_coin("1dcdaa3ae3ce5488ff40cc95362ddb8a15d859cbc1ec68e3aee7dd4f4c1adc6f")

>>> deposit_to_puzzle_hash(pc, cc, bytes32.fromhex("b92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd"))
...
{
    "status": "SUCCESS",
    "success": true
}
```

Our piggybank contribution coins were spent in block **668268**, but we don't see the new piggybank coin because mojos have been set to dummy coin's puzzle hash!

> Even with good intention, any typo or bug in our driver code could also send mojos to invalid puzzle hash and we could lost those mojos forever.

```sh
❯ cdv rpc coinrecords --by id 4ebcd582063a4a3a3ecd3dc5ae6cab14cc6e448ad5e06e26b258e065d571c265         
[
    {
        "coin": {
            "amount": 0,
            "parent_coin_info": "0x926273035e3760dbbf158f560a7dbc248c6683488baac4e04588156f42f8e6fa",
            "puzzle_hash": "0x5c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64"
        },
        "coinbase": false,
        "confirmed_block_index": 659908,
        "spent": true,
        "spent_block_index": 668268,
        "timestamp": 1632932684
    }
]

❯ cdv rpc coinrecords --by id 1dcdaa3ae3ce5488ff40cc95362ddb8a15d859cbc1ec68e3aee7dd4f4c1adc6f         
[
    {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x69b093ab7438df7bfee13e220cc54ddfa92d059c21da1c4ff9ddf9ea8f6e6958",
            "puzzle_hash": "0xe6b571b019744c25e599c0f63593c4003b025c8f437c695b422b13d09bec9107"
        },
        "coinbase": false,
        "confirmed_block_index": 667979,
        "spent": true,
        "spent_block_index": 668268,
        "timestamp": 1633080337
    }
]

# piggybank coin was burn
❯ cdv rpc coinrecords --by puzhash 5c3eba97e05cf431f74f722998c1b8e312d125df49c2e7ecded81e3b830e8f64 -ou
[]

# new dummy coin
❯ cdv rpc coinrecords --by puzhash b92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd -ou -s 668268
[
    {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x4ebcd582063a4a3a3ecd3dc5ae6cab14cc6e448ad5e06e26b258e065d571c265",
            "puzzle_hash": "0xb92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd"
        },
        "coinbase": false,
        "confirmed_block_index": 668268,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1633086218
    }
]
```

### `ASSERT_MY_PUZZLEHASH`

The problem was that we have to rely on the puzzle hash from solution to create a new piggybank coin. Indeed, the puzzle hash of the new coin has to be the same as the current one to meet our requirement. Fortunately, we can add `ASSERT_MY_PUZZLEHASH` condition to make sure the input puzzle hash is the same as the puzzle hash of the coin that contains this puzzle.

Let's check our new piggybank chialisp puzzle:

```lisp
(mod (
        my_amount
        new_amount
        my_puzzlehash
     )
  ...
  (defun-inline recreate_self (new_amount my_puzzlehash)
    (list
      (list CREATE_COIN my_puzzlehash new_amount)
      (list CREATE_PUZZLE_ANNOUNCEMENT "approved")
      (list ASSERT_MY_PUZZLEHASH my_puzzlehash)
    )
  )
  ...
)
```

The puzzle hash for the new piggybank coin is now `2e2546cae60daa0ddfd948bf1d3b783c6fad278e4b5c96b2ad60119807ef2ea7`. So let's see if using dummy coin's puzzle hash fails and using new piggybank coin's puzzle hash works as expected:

```sh
❯ python3 -i ./piggybank_drivers.py
>>> pc = get_coin("4d2a59b2d013dcf84339149173e910932ba1161c5dec16dfb8eecbfbe678f819")
>>> cc = get_coin("b63f0af2ffb57be054ad052995fb71bbc301900d9f7be41d1bfed79ff305e667")
>>> pc
Coin(parent_coin_info=<bytes32: 2f7edc65d5844b8f320aea02fd147f95ecb0737b2be5fdb2e3105cdc7917a974>, puzzle_hash=<bytes32: 2e2546cae60daa0ddfd948bf1d3b783c6fad278e4b5c96b2ad60119807ef2ea7>, amount=0)
>>> cc
Coin(parent_coin_info=<bytes32: d4c554fa571ef8d6fda67e5d6aab1f68ae59aedd25263836b31de927106c05c6>, puzzle_hash=<bytes32: 8b198e66bc96c121341ca38b995af1dcd7e56b10d13fc5b809d38fd7274b2155>, amount=100)
>>> deposit_to_puzzle_hash(pc, cc, bytes32.fromhex("b92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd"))
...
ValueError: {'error': 'Failed to include transaction dd6ffd5bbdc26d1c218061a41a0352878d401c303f8977d18790a1a5e1de3c41, error ASSERT_MY_PUZZLEHASH_FAILED', 'success': False}

>>> deposit_to_puzzle_hash(pc, cc, bytes32.fromhex("2e2546cae60daa0ddfd948bf1d3b783c6fad278e4b5c96b2ad60119807ef2ea7"))
...
{
    "status": "SUCCESS",
    "success": true
}
```

Perfect! Unless we provide the correct puzzle hash (i.e., piggybank's), the spend would not go through.

Our unspent piggybank should have **100** mojos now:

```sh
❯ cdv rpc coinrecords --by puzhash 2e2546cae60daa0ddfd948bf1d3b783c6fad278e4b5c96b2ad60119807ef2ea7
[
    {
        "coin": {
            "amount": 0,
            "parent_coin_info": "0x2f7edc65d5844b8f320aea02fd147f95ecb0737b2be5fdb2e3105cdc7917a974",
            "puzzle_hash": "0x2e2546cae60daa0ddfd948bf1d3b783c6fad278e4b5c96b2ad60119807ef2ea7"
        },
        "coinbase": false,
        "confirmed_block_index": 668980,
        "spent": true,
        "spent_block_index": 669097,
        "timestamp": 1633098878
    },
    {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x4d2a59b2d013dcf84339149173e910932ba1161c5dec16dfb8eecbfbe678f819",
            "puzzle_hash": "0x2e2546cae60daa0ddfd948bf1d3b783c6fad278e4b5c96b2ad60119807ef2ea7"
        },
        "coinbase": false,
        "confirmed_block_index": 669097,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1633100994
    }
]
```


### `my_amount` and `ASSERT_MY_AMOUNT`

As the chialisp itself can't access its coin amount, we need to pass the **current amount** via the solution. However, passing the wrong amount will cause the puzzle works incorrectly. In the code below, you will see that if `my_amount` is not less than `new_amount`, the spend will be invalid. This might not seem to be the issue here, but it might be bigger issue for other puzzles.

```lisp
(mod (
        my_amount
        new_amount
        my_puzzlehash
     )

...
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

Fortunately, we can add an `ASSERT_MY_AMOUNT` condition to make sure accurate **current amount** is used. Before we see the updated code, let's look at another issue.

### `new_amount`

We have used **announcement** to tie piggybank and contribution coins together. We also sanitize **puzzle hash** and **my_amount** inputs. However, bad actors can still steal our mojos if they pass the **new_amount** of the piggybank that less than the sum of contribution coins!

Let's see how the stealing can happen:

```PowerShell
# contribution coins
❯ cdv rpc coinrecords --by puzhash 8b198e66bc96c121341ca38b995af1dcd7e56b10d13fc5b809d38fd7274b2155 -ou -nd `
>> | ConvertFrom-Json -AsHashtable `
>> | % { $_.GetEnumerator() `
>>     | Select-Object @{n='id';e ={$_.name}}`
>>     , @{n='puzzle hash';e={$_.value.coin.puzzle_hash}}`
>>     , @{n='amount'; e={$_.value.coin.amount}}}

id                                                               puzzle hash                                                        amount
--                                                               -----------                                                        ------
a00ad3b203070e14ddaef8a6abd574486d2eae9aa12ef55854c84b096308cb9e 0x8b198e66bc96c121341ca38b995af1dcd7e56b10d13fc5b809d38fd7274b2155    100
7798978816268953fc06e6fbdca1444646c84da0ebb17f84fe70583bc2d3e788 0x8b198e66bc96c121341ca38b995af1dcd7e56b10d13fc5b809d38fd7274b2155    100
0fc2613b732d113fa48cbef5308b43dffbc80eec1c0e3a4149f2c397d566df7e 0x8b198e66bc96c121341ca38b995af1dcd7e56b10d13fc5b809d38fd7274b2155    100

# piggybank coin
❯ cdv rpc coinrecords --by id 396d35e71e5109831545f8c862110017e048fe502222897e61a52d4134989c27 -ou
[
    {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x24dd373dabb4b6d05a1ccede763ca806746527c546a40e839860282c47de16b9",
            "puzzle_hash": "0x2e2546cae60daa0ddfd948bf1d3b783c6fad278e4b5c96b2ad60119807ef2ea7"
        },
        "coinbase": false,
        "confirmed_block_index": 686330,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1633424539
    }
]

# dummy coin
❯ cdv rpc coinrecords --by id 12c0709babe92736387cd4ab8b4082af3aab33422fcc9cd1092ba6f6f6b01b66 -ou
[
    {
        "coin": {
            "amount": 0,
            "parent_coin_info": "0x9795b5b28882e26ee724e546c4c5ba28398f62eb62de9d6be1d4f75f7e29110e",
            "puzzle_hash": "0xb92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd"
        },
        "coinbase": false,
        "confirmed_block_index": 659441,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1632925242
    }
]
```

This time, we will create [a short python script](piggybank/new_amount_demo.py) to help us.

```python
from piggybank_drivers import *

# get existing coins from blockchain
## piggybank coin
pc = get_coin("396d35e71e5109831545f8c862110017e048fe502222897e61a52d4134989c27")

## contribution coins
cc = [
    get_coin("a00ad3b203070e14ddaef8a6abd574486d2eae9aa12ef55854c84b096308cb9e"),
    get_coin("7798978816268953fc06e6fbdca1444646c84da0ebb17f84fe70583bc2d3e788"),
    get_coin("0fc2613b732d113fa48cbef5308b43dffbc80eec1c0e3a4149f2c397d566df7e")
]

## dummy coin
dc = get_coin("12c0709babe92736387cd4ab8b4082af3aab33422fcc9cd1092ba6f6f6b01b66")

# prepare coin spends
contribution_amount = sum([c.amount for c in cc])

cc_solution = solution_for_contribution()
contribution_spends = [CoinSpend(c, CONTRIBUTION_MOD, cc_solution) for c in cc]

piggybank_spend = CoinSpend(
    pc,
    PIGGYBANK_MOD,
    Program.to([pc.amount, 0, pc.puzzle_hash])
)

## steal mojos and put them to a new dummy coin
dummy_spend = CoinSpend(
    dc,
    DUMMY_MOD,
    Program.to([(dc.amount + contribution_amount), dc.puzzle_hash])

)

coin_spends = [cs for cs in contribution_spends]
coin_spends.append(pc)
coin_spends.append(dc)
```

Loading the script above and get the spend bundle to test it. Please note the `new_amount` for both piggybank and dummy coins. Almost all of contribution amount is sent to dummy coin!

```sh
❯ python3 -i ./new_amount-bad.py
>>> contribution_amount
300
>>> piggybank_new_amount
101
>>> dummy_new_amount
299
>>> print_json(spend_bundle.to_json_dict())
{
    "aggregated_signature": "0xc00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "coin_solutions": [
        {
            "coin": {
                "amount": 100,
                "parent_coin_info": "0xef44d8605bf53c84bcb92e68287a78b4fd29cb256689bbb9e990c59d8c4ff122",
                "puzzle_hash": "0x8b198e66bc96c121341ca38b995af1dcd7e56b10d13fc5b809d38fd7274b2155"
            },
            "puzzle_reveal": "0xff02ffff01ff04ffff04ff04ffff04ffff0bff06ffff0188617070726f76656480ff808080ff8080ffff04ffff01ff3fa02e2546cae60daa0ddfd948bf1d3b783c6fad278e4b5c96b2ad60119807ef2ea7ff018080",
            "solution": "0x80"
        },
        {
            "coin": {
                "amount": 100,
                "parent_coin_info": "0x6ccc1057956a6aab91bc8275143457c18e29cc9f40da404b58e85140e936876d",
                "puzzle_hash": "0x8b198e66bc96c121341ca38b995af1dcd7e56b10d13fc5b809d38fd7274b2155"
            },
            "puzzle_reveal": "0xff02ffff01ff04ffff04ff04ffff04ffff0bff06ffff0188617070726f76656480ff808080ff8080ffff04ffff01ff3fa02e2546cae60daa0ddfd948bf1d3b783c6fad278e4b5c96b2ad60119807ef2ea7ff018080",
            "solution": "0x80"
        },
        {
            "coin": {
                "amount": 100,
                "parent_coin_info": "0x620315ae7e3044145be2faf10f649a5318926c69e3a703149047e2053a26d368",
                "puzzle_hash": "0x8b198e66bc96c121341ca38b995af1dcd7e56b10d13fc5b809d38fd7274b2155"
            },
            "puzzle_reveal": "0xff02ffff01ff04ffff04ff04ffff04ffff0bff06ffff0188617070726f76656480ff808080ff8080ffff04ffff01ff3fa02e2546cae60daa0ddfd948bf1d3b783c6fad278e4b5c96b2ad60119807ef2ea7ff018080",
            "solution": "0x80"
        },
        {
            "coin": {
                "amount": 100,
                "parent_coin_info": "0x24dd373dabb4b6d05a1ccede763ca806746527c546a40e839860282c47de16b9",
                "puzzle_hash": "0x2e2546cae60daa0ddfd948bf1d3b783c6fad278e4b5c96b2ad60119807ef2ea7"
            },
            "puzzle_reveal": "0xff02ffff01ff02ffff03ffff15ff0bff0580ffff01ff02ffff03ffff15ff0bff1e80ffff01ff04ffff04ff0affff04ff0cffff04ff0bff80808080ffff04ffff04ff0affff04ff17ffff01ff80808080ffff04ffff04ff16ffff01ff88617070726f7665648080ffff04ffff04ff08ffff04ff17ff808080ff8080808080ffff01ff04ffff04ff0affff04ff17ffff04ff0bff80808080ffff04ffff04ff16ffff01ff88617070726f7665648080ffff04ffff04ff08ffff04ff17ff808080ff8080808080ff0180ffff01ff088080ff0180ffff04ffff01ffff48a0a6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6ff33ff3e8201f4ff018080",
            "solution": "0xff64ff65ffa02e2546cae60daa0ddfd948bf1d3b783c6fad278e4b5c96b2ad60119807ef2ea780"
        },
        {
            "coin": {
                "amount": 0,
                "parent_coin_info": "0x9795b5b28882e26ee724e546c4c5ba28398f62eb62de9d6be1d4f75f7e29110e",
                "puzzle_hash": "0xb92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd"
            },
            "puzzle_reveal": "0xff02ffff01ff04ffff04ff02ffff04ff0bffff04ff05ff80808080ff8080ffff04ffff0133ff018080",
            "solution": "0xff82012bffa0b92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd80"
        }
    ]
}
>>> push_tx(spend_bundle)
{'status': 'SUCCESS', 'success': True}
```

Let's check all of our coins again after the spend bundle is processed:
```sh
❯ cdv rpc coinrecords --by id 396d35e71e5109831545f8c862110017e048fe502222897e61a52d4134989c27 -ou -nd     
{}

❯ cdv rpc coinrecords --by puzhash 8b198e66bc96c121341ca38b995af1dcd7e56b10d13fc5b809d38fd7274b2155 -ou -nd
{}

❯ cdv rpc coinrecords --by puzhash b92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd -ou -nd
{
    ..."d47c35dff3bd1f7473146b064b473a2888eff23bd4bfac19a9ea009a742e5e2b": {
        "coin": {
            "amount": 299,
            "parent_coin_info": "0x12c0709babe92736387cd4ab8b4082af3aab33422fcc9cd1092ba6f6f6b01b66",
            "puzzle_hash": "0xb92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd"
        },
        "coinbase": false,
        "confirmed_block_index": 690069,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1633494500
    }
}

```

We can see that the piggybank and contribution coins are gone and the new dummy coin has all mojos.

### Use ASSERT_PUZZLE_ANNOUCEMENT To Assert Contribution Coin's `my_amount`

Let's see if we can add more **assertions** to address the security issue by the followings:

1. A piggybank coin creates additional announcements for each contribution coin's amount.
2. Every contribution coin asserts an announcement from the piggybank coin of its own amount.

Let's see the updated chialisp code:

#### Piggybank Coin
```lisp
(mod (
        my_amount
        contributions
        my_puzzlehash
     )

  (include condition_codes.clib)

  (defconstant TARGET_AMOUNT 500)
  (defconstant CASH_OUT_PUZZLE_HASH 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6)

  (defun sum (contributions)
    (if (l contributions)
      (+ (f contributions) (sum (r contributions)))
      0
    )
  )

  (defun announce (contributions)
    (if (l contributions)
      (c 
        (list CREATE_PUZZLE_ANNOUNCEMENT (f contributions))
        (announce (r contributions))
      )
      ()
    )
  )

  (defun merge_lists (l1 l2)
    (if (l l1)
        (c (f l1) (merge_lists (r l1) l2))
        l2
    )
  )

  (defun-inline cash_out (CASH_OUT_PUZZLE_HASH contributions my_puzzlehash)
    (merge_lists
      (list
        (list CREATE_COIN CASH_OUT_PUZZLE_HASH (+ my_amount (sum contributions)))
        (list CREATE_COIN my_puzzlehash 0)
        (list ASSERT_MY_PUZZLEHASH my_puzzlehash)
        (list ASSERT_MY_AMOUNT my_amount)
      )
      (announce contributions)
    )
  )

  (defun-inline recreate_self (contributions my_puzzlehash)
    (merge_lists
      (list
        (list CREATE_COIN my_puzzlehash (+ my_amount (sum contributions)))
        (list ASSERT_MY_PUZZLEHASH my_puzzlehash)
        (list ASSERT_MY_AMOUNT my_amount)
      )
      (announce contributions)
    )
  )

  ; main
  (if (> (+ my_amount (sum contributions)) my_amount)
    (if (> (+ my_amount (sum contributions)) TARGET_AMOUNT)
      (cash_out CASH_OUT_PUZZLE_HASH contributions my_puzzlehash)
      (recreate_self contributions my_puzzlehash)
    )
    (x)
  )
)
```

#### Contribution Coin
```lisp
(mod (my_amount)

    (include condition_codes.clib)

    (defconstant PIGGYBANK_PUZZLE_HASH 0x2e2546cae60daa0ddfd948bf1d3b783c6fad278e4b5c96b2ad60119807ef2ea7)

    (list
        (list ASSERT_PUZZLE_ANNOUNCEMENT (sha256 PIGGYBANK_PUZZLE_HASH my_amount))
        (list ASSERT_MY_AMOUNT my_amount)
    )
)
```

### Recursive Function

Before we try to test our new puzzles, let's look at new code. We are not expecting a value, `new_amount`, but `contribution` which is a list of contribution coin's amount. We are able to calculate `new_amount` by summing all amounts in the list, e.g., `(100 150 200)` is **450**.

```lisp
  (defun sum (contributions)
    (if (l contributions)
      (+ (f contributions) (sum (r contributions)))
      0
    )
  )
```
**Chialisp** does not have `for-loop`, so, to iterate through each value in the list, we use **recursion**. We also use other recursive functions to create a list of **annoucements** and merge them with other conditions to get a final list.

```lisp
  (defun announce (contributions)
    (if (l contributions)
      (c 
        (list CREATE_PUZZLE_ANNOUNCEMENT (f contributions))
        (announce (r contributions))
      )
      ()
    )
  )

  (defun merge_lists (l1 l2)
    (if (l l1)
        (c (f l1) (merge_lists (r l1) l2))
        l2
    )
  )
```

### CLVM cost

However, we also need to mind the amount of code in the puzzle. The more code we add to the puzzle, the more associated cost as all full nodes have to run more code. So we should make sure we avoid putting unnecessary code.

Let's compare CLVM cost of our [new and old puzzle](compare).

#### piggybank with `new_amount`
```sh
❯ brun (run ./piggybank.clsp -i ../include) '(100 600 0xcafef00d)' -c --time          
cost = 3133
assemble_from_ir: 0.025092
to_sexp_f: 0.000356
run_program: 0.002596
((51 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 600) (51 0xcafef00d ()) (62 "approved") (72 0xcafef00d))
```

#### piggybank with `contributions`
```sh
❯ brun (run ./piggybank.clsp -i ../include) '(100 (100 200 200) 0xcafef00d)' -c --time
cost = 29792
assemble_from_ir: 0.069140
to_sexp_f: 0.000319
run_program: 0.021761
((51 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 600) (51 0xcafef00d ()) (72 0xcafef00d) (73 100) (62 100) (62 200) (62 200))
```

We just increase the running time almost 10 fold and the puzzle is not totally secured either! :shrug:


### ANNOUNCEMENT Gotcha!

Let's try to break our new puzzle by contributing **150**, **200**, and two **100** mojo coins:

```sh
❯ python3 -i ./piggybank_drivers.py
>>> PIGGYBANK_MOD.get_tree_hash()
<bytes32: d02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d>
>>> CONTRIBUTION_MOD.get_tree_hash()
<bytes32: 6aae6f4638981ba070d1f4b7ba5fa091ccec531369165ffe222aa868816a695d>
```

#### Piggybank Coin
```sh
❯ cdv rpc coinrecords --by puzhash d02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d -ou -nd
{
    "70a721759d9d3a6a200c32ef36cc72d8cb440f5149d9d9e68f82bf97f25ecc0d": {
        "coin": {
            "amount": 0,
            "parent_coin_info": "0xce16680ed68ddafa6d54258c2cdafcca4c0181e29fb5993a8572c787670e67e8",
            "puzzle_hash": "0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d"
        },
        "coinbase": false,
        "confirmed_block_index": 713007,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1633926825
    }
}
```

#### Contribution Coins
```sh
❯ cdv rpc coinrecords --by puzhash  6aae6f4638981ba070d1f4b7ba5fa091ccec531369165ffe222aa868816a695d -ou -nd
{
    "3bb538b58ae8c2d703f03a2ffab53a5565b36d44d3a38b94ed7fd482a9d07681": {
        "coin": {
            "amount": 150,
            "parent_coin_info": "0x9834d182141244019b55795806dda1a5c70d4d733dfa2d9ca5b008f6eec3ba34",
            "puzzle_hash": "0x6aae6f4638981ba070d1f4b7ba5fa091ccec531369165ffe222aa868816a695d"
        },
        "coinbase": false,
        "confirmed_block_index": 713096,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1633928555
    },
    "5fdf91cfd695f3b7f90f3d89a9e98b950684af41c3a08c9272e8499eb157b502": {
        "coin": {
            "amount": 200,
            "parent_coin_info": "0x55d6ed6dac75250dba194efa1e22400c5a22ae5f0b604496c5166d05be1fd1ec",
            "puzzle_hash": "0x6aae6f4638981ba070d1f4b7ba5fa091ccec531369165ffe222aa868816a695d"
        },
        "coinbase": false,
        "confirmed_block_index": 713088,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1633928459
    },
    "9bd47da5c7547671a7f343837f72090b93846ab714fdb8de5b915bdc6d223d7b": {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x901b513acb9751ac2e52e46d8648f28f442711d016be9419756f4bd39e4669a5",
            "puzzle_hash": "0x6aae6f4638981ba070d1f4b7ba5fa091ccec531369165ffe222aa868816a695d"
        },
        "coinbase": false,
        "confirmed_block_index": 713076,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1633928125
    },
    "f1676b72da59a8687afd5776d02bfb49d0b4fcdae5c0c0b6d7c987bf63013cd0": {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x4fad6d1eb0dedca392ca93a971271905fbe22c7638185251b13cab396b139301",
            "puzzle_hash": "0x6aae6f4638981ba070d1f4b7ba5fa091ccec531369165ffe222aa868816a695d"
        },
        "coinbase": false,
        "confirmed_block_index": 713103,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1633928656
    }
}
```

#### Dummy Coin
```sh
❯ cdv rpc coinrecords --by puzhash b92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd -ou -nd
{
    "86052ac34f41224c12ed2dfc41a690ab470f2a5779698d32c3a0ffacda3f6737": {
        "coin": {
            "amount": 100,
            "parent_coin_info": "0x4ebcd582063a4a3a3ecd3dc5ae6cab14cc6e448ad5e06e26b258e065d571c265",
            "puzzle_hash": "0xb92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd"
        },
        "coinbase": false,
        "confirmed_block_index": 668268,
        "spent": false,
        "spent_block_index": 0,
        "timestamp": 1633086218
}
```

#### Spending

```python
from piggybank_drivers import *

## contribution coins
cc150 = get_coin("3bb538b58ae8c2d703f03a2ffab53a5565b36d44d3a38b94ed7fd482a9d07681")
cc150_solution = Program.to([cc150.amount])
cc150_spend = CoinSpend(
    cc150,
    CONTRIBUTION_MOD,
    cc150_solution
)

cc200 = get_coin("5fdf91cfd695f3b7f90f3d89a9e98b950684af41c3a08c9272e8499eb157b502")
cc200_solution = Program.to([cc200.amount])
cc200_spend = CoinSpend(
    cc200,
    CONTRIBUTION_MOD,
    cc200_solution
)

cc100_1 = get_coin("9bd47da5c7547671a7f343837f72090b93846ab714fdb8de5b915bdc6d223d7b")
cc100_1_solution = Program.to([cc100_1.amount])
cc100_1_spend = CoinSpend(
    cc100_1,
    CONTRIBUTION_MOD,
    cc100_1_solution
)

cc100_2 = get_coin("f1676b72da59a8687afd5776d02bfb49d0b4fcdae5c0c0b6d7c987bf63013cd0")
cc100_2_solution = Program.to([cc100_2.amount])
cc100_2_spend = CoinSpend(
    cc100_2,
    CONTRIBUTION_MOD,
    cc100_2_solution
)


## piggybank coin
pc = get_coin("70a721759d9d3a6a200c32ef36cc72d8cb440f5149d9d9e68f82bf97f25ecc0d")
pc_solution = Program.to([pc.amount, [150, 200, 100], pc.puzzle_hash])
pc_spend = CoinSpend(
    pc,
    PIGGYBANK_MOD,
    pc_solution
)

## dummy coin
dc = get_coin("86052ac34f41224c12ed2dfc41a690ab470f2a5779698d32c3a0ffacda3f6737")
dc_solution = Program.to([100, dc.puzzle_hash])
dc_spend = CoinSpend(
    dc,
    DUMMY_MOD,
    dc_solution
)

coin_spends = [
    pc_spend,
    cc150_spend, cc200_spend, cc100_1_spend, cc100_2_spend,
    dc_spend
]

spend_bundle = SpendBundle(coin_spends, G2Element())
```

#### Inspecting The Spend Bundle

Pushing the [spend bundle](spend_bundles/contributions-bad-but-work.json) doesn't give us any error as expected although we spend four contribution coins but only amount from three coins are provided to the piggybank coin's puzzle. 

> **100** mojo goes to the farmer as a fee in this case, `cdv rpc blockrecords -i 713274`

Inspecting the spend bundle gives us some clues. The issue is that the two **100** mojo contribution coins are asserting the same announcement, `0x8b55d5d225df0f4b9c0c7b44c53b27c2c03014deb6119ff8f99119329166f4bf`. Although the piggybank coin announces only once, the condition is valid for both contribution coin. 


```sh
❯ cdv inspect spendbundles ./spend_bundles/contributions-bad-but-work.json -db
...
grouped conditions:

  (CREATE_COIN 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d 450)

  (ASSERT_MY_PUZZLEHASH 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d)

  (ASSERT_MY_AMOUNT ())

  (CREATE_PUZZLE_ANNOUNCEMENT 150)
  (CREATE_PUZZLE_ANNOUNCEMENT 200)
  (CREATE_PUZZLE_ANNOUNCEMENT 100)


-------
consuming coin (0x9834d182141244019b55795806dda1a5c70d4d733dfa2d9ca5b008f6eec3ba34 0x6aae6f4638981ba070d1f4b7ba5fa091ccec531369165ffe222aa868816a695d 150)
  with id 3bb538b58ae8c2d703f03a2ffab53a5565b36d44d3a38b94ed7fd482a9d07681


brun -y main.sym '(a (q 4 (c 10 (c (sha256 14 5) ())) (c (c 4 (c 5 ())) ())) (c (q 73 63 . 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d) 1))' '(150)'

((ASSERT_PUZZLE_ANNOUNCEMENT 0x3b0f501d6cf7aeca1c1b1e627e889afc895c7d6e511dc19e27026dd1482ca262) (ASSERT_MY_AMOUNT 150))

grouped conditions:

  (ASSERT_PUZZLE_ANNOUNCEMENT 0x3b0f501d6cf7aeca1c1b1e627e889afc895c7d6e511dc19e27026dd1482ca262)

  (ASSERT_MY_AMOUNT 150)


-------
consuming coin (0x55d6ed6dac75250dba194efa1e22400c5a22ae5f0b604496c5166d05be1fd1ec 0x6aae6f4638981ba070d1f4b7ba5fa091ccec531369165ffe222aa868816a695d 200)
  with id 5fdf91cfd695f3b7f90f3d89a9e98b950684af41c3a08c9272e8499eb157b502


brun -y main.sym '(a (q 4 (c 10 (c (sha256 14 5) ())) (c (c 4 (c 5 ())) ())) (c (q 73 63 . 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d) 1))' '(200)'

((ASSERT_PUZZLE_ANNOUNCEMENT 0x71fb2bcd16d3354848f272cfe6567508f74911231e8abf466feba0d56376055d) (ASSERT_MY_AMOUNT 200))

grouped conditions:

  (ASSERT_PUZZLE_ANNOUNCEMENT 0x71fb2bcd16d3354848f272cfe6567508f74911231e8abf466feba0d56376055d)

  (ASSERT_MY_AMOUNT 200)


-------
consuming coin (0x901b513acb9751ac2e52e46d8648f28f442711d016be9419756f4bd39e4669a5 0x6aae6f4638981ba070d1f4b7ba5fa091ccec531369165ffe222aa868816a695d 100)
  with id 9bd47da5c7547671a7f343837f72090b93846ab714fdb8de5b915bdc6d223d7b


brun -y main.sym '(a (q 4 (c 10 (c (sha256 14 5) ())) (c (c 4 (c 5 ())) ())) (c (q 73 63 . 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d) 1))' '(100)'

((ASSERT_PUZZLE_ANNOUNCEMENT 0x8b55d5d225df0f4b9c0c7b44c53b27c2c03014deb6119ff8f99119329166f4bf) (ASSERT_MY_AMOUNT 100))

grouped conditions:

  (ASSERT_PUZZLE_ANNOUNCEMENT 0x8b55d5d225df0f4b9c0c7b44c53b27c2c03014deb6119ff8f99119329166f4bf)

  (ASSERT_MY_AMOUNT 100)


-------
consuming coin (0x4fad6d1eb0dedca392ca93a971271905fbe22c7638185251b13cab396b139301 0x6aae6f4638981ba070d1f4b7ba5fa091ccec531369165ffe222aa868816a695d 100)
  with id f1676b72da59a8687afd5776d02bfb49d0b4fcdae5c0c0b6d7c987bf63013cd0


brun -y main.sym '(a (q 4 (c 10 (c (sha256 14 5) ())) (c (c 4 (c 5 ())) ())) (c (q 73 63 . 0xd02db06d715c2b44ee1945ab7950996b220808e178e7122f71b316d0e2f7410d) 1))' '(100)'

((ASSERT_PUZZLE_ANNOUNCEMENT 0x8b55d5d225df0f4b9c0c7b44c53b27c2c03014deb6119ff8f99119329166f4bf) (ASSERT_MY_AMOUNT 100))

grouped conditions:

  (ASSERT_PUZZLE_ANNOUNCEMENT 0x8b55d5d225df0f4b9c0c7b44c53b27c2c03014deb6119ff8f99119329166f4bf)

  (ASSERT_MY_AMOUNT 100)


-------
consuming coin (0x4ebcd582063a4a3a3ecd3dc5ae6cab14cc6e448ad5e06e26b258e065d571c265 0xb92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd 100)
  with id 86052ac34f41224c12ed2dfc41a690ab470f2a5779698d32c3a0ffacda3f6737


brun -y main.sym '(a (q 4 (c 2 (c 11 (c 5 ()))) ()) (c (q . 51) 1))' '(100 0xb92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd)'

((CREATE_COIN 0xb92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd 100))

grouped conditions:

  (CREATE_COIN 0xb92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd 100)


...

created  puzzle announcements = ['3b0f501d6cf7aeca1c1b1e627e889afc895c7d6e511dc19e27026dd1482ca262', '71fb2bcd16d3354848f272cfe6567508f74911231e8abf466feba0d56376055d', '8b55d5d225df0f4b9c0c7b44c53b27c2c03014deb6119ff8f99119329166f4bf']

asserted puzzle announcements = ['3b0f501d6cf7aeca1c1b1e627e889afc895c7d6e511dc19e27026dd1482ca262', '71fb2bcd16d3354848f272cfe6567508f74911231e8abf466feba0d56376055d', '8b55d5d225df0f4b9c0c7b44c53b27c2c03014deb6119ff8f99119329166f4bf', '8b55d5d225df0f4b9c0c7b44c53b27c2c03014deb6119ff8f99119329166f4bf']

symdiff of puzzle announcements = []
...
```

## Conclusions

We have been trying to secure our coins by using `ASSERT_MY_AMOUNT` and `ASSERT_MY_PUZZLEHASH`. Also we try to verify the contribution coin amount by using **annoucement**. However, our coins are still not secure and bad actors can still steal our contribution coins even though we have code that increases the CLVM costs by 10x.

## References

- [chialsip.com | 8 - Security](https://chialisp.com/docs/security)
- [tutorial | 4 - Securing a Smart Coin](https://youtu.be/_SBGfMZhRd8)
- [High Level Tips 1 - Managing State, Coin Creation, Announcements](https://www.youtube.com/watch?v=lDXB4NlbQ-E)
- [High Level Tips 2 - Security, Checking Arguments & Signatures](https://www.youtube.com/watch?v=T4noZyNJkFA)
