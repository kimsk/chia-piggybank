# Securing Piggybank Coin (ASSERT_MY_*)

In the [last post](POST-4.md), we are able to guarantee that our contribution coins have to be spent together with our designated piggybank coin by aseerting puzzle annoucement.

However, the existing piggybank coin still has issues allowing bad actors to steal our mojos. Let's look at those issues together:

## Problem With Piggybank Solution

### `my_puzzlehash`

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
]
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

The problem was that we have to rely on the puzzle hash from solution to create a new piggybank coin. Indeed, the puzzle hash of the new coin has to be the same as the current one to meet our requirement. Fortunately, we can force this by adding `ASSERT_MY_PUZZLEHASH` condition to make sure the input puzzle hash is the same as the puzzle hash of the coin that contains this puzzle.

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

## References

- [chialsip.com | 8 - Security](https://chialisp.com/docs/security)
- [tutorial | 4 - Securing a Smart Coin](https://youtu.be/_SBGfMZhRd8)
- [High Level Tips 1 - Managing State, Coin Creation, Announcements](https://www.youtube.com/watch?v=lDXB4NlbQ-E)
- [High Level Tips 2 - Security, Checking Arguments & Signatures](https://www.youtube.com/watch?v=T4noZyNJkFA)
