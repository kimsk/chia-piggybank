# ANNOUNCEMENT & coin id

We still have [annoucement issue](https://github.com/kimsk/chia-piggybank/blob/main/POST-5.md#announcement-gotcha) because different coins expect the same announcement message. To resolve that, we have to add some unique data to differentiate expected annoucenment for different coins. We could do that by adding `coin_id` in the annoucenment.

Let's see the updated code for contribution coin:

```lisp
(mod (my_coin_id my_amount)

    (include condition_codes.clib)

    (defconstant PIGGYBANK_PUZZLE_HASH 0x7383903f3da7d044146aef59fec5dac0da98c6ae427b7c14d3e22ebd548a4257)
    (defconstant PUBKEY 0xa0f10c708a8ef327c117fbf2676ed2c19e6d4c05e1d731fed759760f5a3be8d0372780025d7d8fba008bef49ef61a6f1)

    (list
        (list ASSERT_PUZZLE_ANNOUNCEMENT (sha256 PIGGYBANK_PUZZLE_HASH (sha256 my_coin_id my_amount)))
        (list ASSERT_MY_AMOUNT my_amount)
        (list ASSERT_MY_COIN_ID my_coin_id)
        (list AGG_SIG_ME PUBKEY (sha256 my_amount))
    )
)
```

Now the coin is expecting the annoucement message to be a hash of `coin_id` and `amount`.


```sh
❯ cdv rpc coinrecords --by puzhash 7383903f3da7d044146aef59fec5dac0da98c6ae427b7c14d3e22ebd548a4257 -ou -nd
{
    "74122f64aea8c9addd228d6d8096bb7353fb895dc77e9794d6ee71529211d169": {
        "coin": {
            "amount": 0,
            "parent_coin_info": "0xc695baf841458c9b1646f337ac78b84921fe10f115a01f32dcd0094c72732ad5",
            "puzzle_hash": "0x7383903f3da7d044146aef59fec5dac0da98c6ae427b7c14d3e22ebd548a4257"
        },...
    }
}

❯ cdv rpc coinrecords --by puzhash 1b09eef0781c9587b167d99a7c4730746735a19b893fd3f53e5bc890454c540e -ou
-nd
{
    "46564cec8e013310b4deee4d357c873a8d642bc807dafac165d3c2045fe06680": {
        "coin": {
            "amount": 300000000,
            "parent_coin_info": "0x51389c474ae9843e0acd2b4f02d6e9fa1b0a66985e8f3cc3b02e2d59a75cb418",
            "puzzle_hash": "0x1b09eef0781c9587b167d99a7c4730746735a19b893fd3f53e5bc890454c540e"
        },...
    },
    "94115a9ec073588f67c997c785609077256fe1ce9e3ecbdabfe8576e50bcbaa3": {
        "coin": {
            "amount": 100000000,
            "parent_coin_info": "0x721e1b4ac3d39234735d42d3b03194c0ba15b0c4a86f3724ba4de9c5b2aa5810",
            "puzzle_hash": "0x1b09eef0781c9587b167d99a7c4730746735a19b893fd3f53e5bc890454c540e"
        },...
    },
    "ab800c725ee21f1afc180793270df17e8b2b6c98395d29b534cc22d476a18ceb": {
        "coin": {
            "amount": 100000000,
            "parent_coin_info": "0xe79a1bb610b98934dc1a040ec35f547d90b66fd61fd2bc268916670aa37957a8",
            "puzzle_hash": "0x1b09eef0781c9587b167d99a7c4730746735a19b893fd3f53e5bc890454c540e"
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
cc = get_coin("ab800c725ee21f1afc180793270df17e8b2b6c98395d29b534cc22d476a18ceb")
cc_solution = Program.to([cc.name(), cc.amount])
cc_spend = CoinSpend(
    cc,
    CONTRIBUTION_MOD,
    cc_solution
)
# 300000000
cc2 = get_coin("46564cec8e013310b4deee4d357c873a8d642bc807dafac165d3c2045fe06680")
cc_solution2 = Program.to([cc2.name(), cc2.amount])
cc_spend2 = CoinSpend(
    cc2,
    CONTRIBUTION_MOD,
    cc_solution2
)

# 100000000
cc3 = get_coin("94115a9ec073588f67c997c785609077256fe1ce9e3ecbdabfe8576e50bcbaa3")
cc_solution3 = Program.to([cc3.name(), cc3.amount])
cc_spend3 = CoinSpend(
    cc3,
    CONTRIBUTION_MOD,
    cc_solution3
)

## piggybank coin
## only cc and cc2 are contributed, cc3 would be spent as fees
pc = get_coin("74122f64aea8c9addd228d6d8096bb7353fb895dc77e9794d6ee71529211d169")
pc_solution = Program.to(
    [pc.amount, 
    [
        [cc.name(), cc.amount],
        [cc2.name(), cc2.amount], 
        #[cc3.name(), cc3.amount]
    ],
    pc.puzzle_hash]
)
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
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
                )

sig2: G2Element = AugSchemeMPL.sign(sk,
                    std_hash(int_to_bytes(cc2.amount))
                    + cc2.name()
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
                )

sig3: G2Element = AugSchemeMPL.sign(sk,
                    std_hash(int_to_bytes(cc3.amount))
                    + cc3.name()
                    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
                )

sig = AugSchemeMPL.aggregate([sig1, sig2, sig3])

spend_bundle = SpendBundle(coin_spends, sig)
print_json(spend_bundle.to_json_dict(include_legacy_keys = False, exclude_modern_keys = False))
```

```sh
❯ cdv inspect spendbundles ./announcement_coin_id_amount.json -db                      
...

created  puzzle announcements = ['78c50a3a6ef46f9e8b03a23b6325edb5879197a569d6d49ed6404c4f478e69a7', 'fdd958dbde2374dadb01ad2bf850c243b220488634308556836d8cf20b751c56']

asserted puzzle announcements = ['3674fd32a00667fa0eccb1758bd42eeb08676c5c1be996fda2f1a92b823dd36b', '78c50a3a6ef46f9e8b03a23b6325edb5879197a569d6d49ed6404c4f478e69a7', 'fdd958dbde2374dadb01ad2bf850c243b220488634308556836d8cf20b751c56']

symdiff of puzzle announcements = ['3674fd32a00667fa0eccb1758bd42eeb08676c5c1be996fda2f1a92b823dd36b']


================================================================================

aggregated signature check pass: True
...

❯ cdv rpc pushtx ./announcement_coin_id_amount.json                                    
("{'error': 'Failed to include transaction "
 '22e4612a13d34926ba51d6c8850d8099e7f3fb85df95eb0470050cffd6a140d0, error '
 "ASSERT_ANNOUNCE_CONSUMED_FAILED', 'success': False}")
```

Now if we do not include all contribution coins in the solution of the piggybank coin, the announcement requirement for the spend bundle will not be met.

# Cost & Fees

However, even the announcement requirement are met, we still can't spend the bundle!

```sh
❯ cdv rpc pushtx ./announcement_coin_id_amount.json                                    
("{'error': 'Failed to include transaction "
 'ab9193f1d509a99098213f5d2f17b66881bcd3d0fbc0d5f02ea34d2d9652605f, error '
 "INVALID_FEE_TOO_CLOSE_TO_ZERO', 'success': False}")
```



```sh
brun (run ./piggybank.clsp -i ../include) '(100 (100 200 200) 
```


## Conclusions

Now our contribution coins can only be spent by a user with a designated secret key. And we also resolve the annoucement issue!