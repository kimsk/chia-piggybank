# Driver Code

After we have chialisp puzzle, the next steps are to deploy them and interact (e.g., spend) with those coins. However, as we can see from the previous posts, the manual steps are very error-prone and cumbersome. Fortunately, we can write code to perform all of those steps.

## Manual Steps

First, let's look all the manual steps we have to do. 

### get the puzzle hash and address

```sh
❯ cdv clsp treehash ./piggybank/piggybank.clsp.hex
❯ cdv encode (cdv clsp treehash ./piggybank/piggybank.clsp.hex) --prefix txch
```
### deploy
```sh
chia wallet send -a 0 -t txch1cg6n9h0mp4ux2n8h86dpuk6p0lrucygdgr9cczqe34s9wpjwkluqaq07sn --override -f 3919172776
```

### spend bundle
In this step, using `opc`, you have to get serialized `puzzle_reveal` and `solution` for each coin in the spend bundle. Below is how to get serialized `solution` manually:

```sh
❯ opc '(0 100 0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8)'
ff80ff64ffa0c23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f880
```

In addition, we have to make sure we provide correct coin information otherwise the spend bundle would be invalid. To do that manually, we have to get coin information via RPC or `cdv rpc` commands and make a note of `parent_coin_info`, `puzzle_hash` and `amount`.

### push transaction to blockchain

After painstaking creting the spend bundle, the last step is to push the spend bundle to the blockchain and cross our fingers.


```sh
❯ cdv rpc pushtx ./spend_bundle-100.json
```

## Driver Code

Fortunately, we can do all the steps above via another program. Chia blockchain and many of associated tools and libraries are written in Python, so we could utilize those code to write a Python program (called a driver code) to loading puzzle, getting puzzle hash, encoding/decoding, or talking with the full node or wallet.

The sample code from the [Driver Code](https://www.youtube.com/watch?v=dGohmAc658c) tutorial video is a good start, but we can do better. The driver code is [here](https://github.com/kimsk/chia-piggybank/blob/c8bdd9cc3eead4bac816ae0afd34e0358f834e6a/piggybank/piggybank_drivers.py), but let's see some exmaples:

### get the puzzle hash and address

```python
# load coins (compiled and serialized, same content as clsp.hex)
mod = load_clvm(clsp_file, package_or_requirement=__name__, search_paths=["../include"]) 
# cdv clsp treehash
treehash = mod.get_tree_hash()
# cdv encode
address = encode_puzzle_hash(treehash, "txch")
```
### deploy (send money) and get coin information

```python
# create a wallet client
wallet_client = await WalletRpcClient.create(
        self_hostname, uint16(wallet_rpc_port), DEFAULT_ROOT_PATH, config
    )

# send standard transaction
res = await wallet_client.send_transaction(wallet_id, amount, address, fee)
tx_id = res.name

# wait until transaction is confirmed
tx: TransactionRecord = await wallet_client.get_transaction(wallet_id, tx_id)
while (not tx.confirmed):
    await asyncio.sleep(5)
    tx = await wallet_client.get_transaction(wallet_id, tx_id)

# get coin infos including coin id of the addition with the same puzzle hash
puzzle_hash = decode_puzzle_hash(address)
coin = next((c for c in tx.additions if c.puzzle_hash == puzzle_hash), None)
```

### build and push the spend bundle (deposit)

```python
def deposit(piggybank_coin: Coin, contribution_coins):
    if type(contribution_coins) != list:
        contribution_coins: list = [contribution_coins]

    contribution_amount = sum([c.amount for c in contribution_coins])

    # coin information, puzzle_reveal, and solution
    piggybank_spend = CoinSpend(
        piggybank_coin,
        PIGGYBANK_MOD,
        solution_for_piggybank(piggybank_coin, contribution_amount)
    )

    cc_puzzle = CONTRIBUTION_MOD
    cc_solution = solution_for_contribution()
    contribution_spends = [CoinSpend(c, cc_puzzle, cc_solution) for c in contribution_coins]

    # empty signature i.e., c00000.....
    signature = G2Element()

    coin_spends = [cs for cs in contribution_spends]
    coin_spends.append(piggybank_spend)
    # SpendBundle
    spend_bundle = SpendBundle(
            # coin spends
            coin_spends,
            # aggregated_signature
            signature,
        )
    status = push_tx(spend_bundle)
```

## Run Driver Code

We can see how it works step by step via Python REPL. Let's start with deploying `piggybank coin` and three `contribution coins` of **100**, **200**, and **300** mojos.

### deploy piggybank coin
```sh
❯ python3 -i ./piggybank_drivers.py
>>> piggybank = deploy_smart_coin(PIGGYBANK_CLSP, 0)
sending 0 to txch1cg6n9h0mp4ux2n8h86dpuk6p0lrucygdgr9cczqe34s9wpjwkluqaq07sn...
waiting until transaction 7d7bb0e6f7acc7674f5f42b5fb9602c1446d1453d61605d557c575a56e6762e4 is confirmed...
......
tx 7d7bb0e6f7acc7674f5f42b5fb9602c1446d1453d61605d557c575a56e6762e4 is confirmed.
coin {'amount': 0,
 'parent_coin_info': '0x716e6c44fe1819059e785403711d8fbfad76ce36d4a7f51ffe9b07fa2c34fb91',
 'puzzle_hash': '0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8'}
deploy piggybank.clsp with 0 mojos to c23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8 in 30.13 seconds.
coin_id: a61eb63b0206e1ced64d3c3becc054ebf3dcf43ad3d4ea78c4a685844ed1af8c
>>>
```

## deploy contribution coins
```sh
>>> contribution_100 = deploy_smart_coin(CONTRIBUTION_CLSP, 100)
sending 100 to txch1f063yte5g42v2w7796ace54hu0gkqzkkx8pctfwhen3rcau9gkdqpsnmae...
waiting until transaction d529f29d7ce544df87066f3b06cfb854c59841359c3221ddde2776b96b9cd3e3 is confirmed...
............
tx d529f29d7ce544df87066f3b06cfb854c59841359c3221ddde2776b96b9cd3e3 is confirmed.
coin {'amount': 100,
 'parent_coin_info': '0xd11ed3514ec5452cd5b98ca06c0072e4f5f38a2a9fb58bf3ce002132b143c32e',
 'puzzle_hash': '0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a'}
deploy contribution.clsp with 100 mojos to 4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a in 60.17 seconds.
coin_id: ad65797cd26018efb0ef8903532124704749b71bd77e765ebd19ad0cb7f5cd9c
>>> contribution_200 = deploy_smart_coin(CONTRIBUTION_CLSP, 200)
sending 200 to txch1f063yte5g42v2w7796ace54hu0gkqzkkx8pctfwhen3rcau9gkdqpsnmae...
waiting until transaction e113f906c35a7d9ba9b2da4eead2d62dd6b800384f0decea03ced52c2459ab80 is confirmed...
..............
tx e113f906c35a7d9ba9b2da4eead2d62dd6b800384f0decea03ced52c2459ab80 is confirmed.
coin {'amount': 200,
 'parent_coin_info': '0xed5e4ec1aa8bc8070bcb4ea9099151609900ca6fa2ee680f9e017162a2530bbe',
 'puzzle_hash': '0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a'}
deploy contribution.clsp with 200 mojos to 4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a in 70.18 seconds.
coin_id: f7e38810b8570f63c49f88632af8171af55bdbed18a907eaf680ac6e1a570f56
>>> contribution_300 = deploy_smart_coin(CONTRIBUTION_CLSP, 300)
sending 300 to txch1f063yte5g42v2w7796ace54hu0gkqzkkx8pctfwhen3rcau9gkdqpsnmae...
waiting until transaction 88338e96d270e5a4fca28a782debb2dad038426dbd546adace8ced0a23dd8ab8 is confirmed...
..............
tx 88338e96d270e5a4fca28a782debb2dad038426dbd546adace8ced0a23dd8ab8 is confirmed.
coin {'amount': 300,
 'parent_coin_info': '0x05ea529a7c9c3d4b67fea1449d977dbb4bc685686b232c8d32c499a39f5bc1c3',
 'puzzle_hash': '0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a'}
deploy contribution.clsp with 300 mojos to 4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a in 70.30 seconds.
coin_id: 66dc36a6dbe5a598e403821f43e38840fa67de0af28449537122498ad03e0efc
```

### get coin records from testnet7 block 570135
```sh
❯ cdv rpc coinrecords --by puzhash 0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8 -ou -s 570135
[{'coin': {'amount': 0,
           'parent_coin_info': '0x716e6c44fe1819059e785403711d8fbfad76ce36d4a7f51ffe9b07fa2c34fb91',
           'puzzle_hash': '0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8'},
  'coinbase': False,
  'confirmed_block_index': 570137,
  'spent': False,
  'spent_block_index': 0,
  'timestamp': 1631258579}]

chia-piggybank/piggybank on  main [!?] via 🐍 v3.8.10
❯ cdv rpc coinrecords --by puzhash 0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a -ou -s 570135
[{'coin': {'amount': 200,
           'parent_coin_info': '0xed5e4ec1aa8bc8070bcb4ea9099151609900ca6fa2ee680f9e017162a2530bbe',
           'puzzle_hash': '0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a'},
  'coinbase': False,
  'confirmed_block_index': 570152,
  'spent': False,
  'spent_block_index': 0,
  'timestamp': 1631259075},
 {'coin': {'amount': 300,
           'parent_coin_info': '0x05ea529a7c9c3d4b67fea1449d977dbb4bc685686b232c8d32c499a39f5bc1c3',
           'puzzle_hash': '0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a'},
  'coinbase': False,
  'confirmed_block_index': 570278,
  'spent': False,
  'spent_block_index': 0,
  'timestamp': 1631261280},
 {'coin': {'amount': 100,
           'parent_coin_info': '0xd11ed3514ec5452cd5b98ca06c0072e4f5f38a2a9fb58bf3ce002132b143c32e',
           'puzzle_hash': '0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a'},
  'coinbase': False,
  'confirmed_block_index': 570140,
  'spent': False,
  'spent_block_index': 0,
  'timestamp': 1631258676}]
```

### deposit **100** mojos

After all smart coins are on the blockchain, we can push the spend bundles to deposit mojos to the piggybank coin.

```sh
❯ python3 -i ./piggybank_drivers.py
>>> piggybank = get_coin("a61eb63b0206e1ced64d3c3becc054ebf3dcf43ad3d4ea78c4a685844ed1af8c")
>>> contribution_100 = get_coin("ad65797cd26018efb0ef8903532124704749b71bd77e765ebd19ad0cb7f5cd9c")
>>> deposit(piggybank, contribution_100)
{
    "aggregated_signature": "0xc00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "coin_spends": [
        {
            "coin": {
                "amount": 0,
                "parent_coin_info": "0x716e6c44fe1819059e785403711d8fbfad76ce36d4a7f51ffe9b07fa2c34fb91",
                "puzzle_hash": "0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8"
            },
            "puzzle_reveal": "0xff02ffff01ff02ffff03ffff15ff0bff0580ffff01ff02ffff03ffff15ff0bff0e80ffff01ff04ffff04ff0affff04ff04ffff04ff0bff80808080ffff04ffff04ff0affff04ff17ffff01ff80808080ff808080ffff01ff04ffff04ff0affff04ff17ffff04ff0bff80808080ff808080ff0180ffff01ff088080ff0180ffff04ffff01ffa0a6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6ff338201f4ff018080",
            "solution": "0xff80ff64ffa0c23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f880"
        },
        {
            "coin": {
                "amount": 100,
                "parent_coin_info": "0xd11ed3514ec5452cd5b98ca06c0072e4f5f38a2a9fb58bf3ce002132b143c32e",
                "puzzle_hash": "0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a"
            },
            "puzzle_reveal": "0x80",
            "solution": "0x80"
        }
    ]
}
{
    "status": "SUCCESS",
    "success": true
}
```

### new piggybank
```sh
❯ cdv rpc coinrecords --by puzhash 0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8 -ou -s 570135 -nd
{'03e630b3f0f5aa28d208ec3c27be3ac4398c3757e2d8aa09a0dc907d8667db79': {'coin': {'amount': 100,
                                                                               'parent_coin_info': '0xa61eb63b0206e1ced64d3c3becc054ebf3dcf43ad3d4ea78c4a685844ed1af8c',
                                                                               'puzzle_hash': '0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8'},
                                                                      'coinbase': False,
                                                                      'confirmed_block_index': 570794,
                                                                      'spent': False,
                                                                      'spent_block_index': 0,
                                                                      'timestamp': 1631271348}}
```

### deposit **200** and **300** mojo coins
```sh
>>> piggybank = get_coin("03e630b3f0f5aa28d208ec3c27be3ac4398c3757e2d8aa09a0dc907d8667db79")
>>> piggybank
Coin(parent_coin_info=<bytes32: a61eb63b0206e1ced64d3c3becc054ebf3dcf43ad3d4ea78c4a685844ed1af8c>, puzzle_hash=<bytes32: c23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8>, amount=100)
```


```sh
>>> piggybank = get_coin("03e630b3f0f5aa28d208ec3c27be3ac4398c3757e2d8aa09a0dc907d8667db79")
>>> piggybank
Coin(parent_coin_info=<bytes32: a61eb63b0206e1ced64d3c3becc054ebf3dcf43ad3d4ea78c4a685844ed1af8c>, puzzle_hash=<bytes32: c23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8>, amount=100)
>>> contribution_200 = get_coin("f7e38810b8570f63c49f88632af8171af55bdbed18a907eaf680ac6e1a570f56")
>>> deposit(piggybank, contribution_200)
{
    "aggregated_signature": "0xc00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "coin_spends": [
        {
            "coin": {
                "amount": 100,
                "parent_coin_info": "0xa61eb63b0206e1ced64d3c3becc054ebf3dcf43ad3d4ea78c4a685844ed1af8c",
                "puzzle_hash": "0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8"
            },
            "puzzle_reveal": "0xff02ffff01ff02ffff03ffff15ff0bff0580ffff01ff02ffff03ffff15ff0bff0e80ffff01ff04ffff04ff0affff04ff04ffff04ff0bff80808080ffff04ffff04ff0affff04ff17ffff01ff80808080ff808080ffff01ff04ffff04ff0affff04ff17ffff04ff0bff80808080ff808080ff0180ffff01ff088080ff0180ffff04ffff01ffa0a6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6ff338201f4ff018080",
            "solution": "0xff64ff82012cffa0c23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f880"
        },
        {
            "coin": {
                "amount": 200,
                "parent_coin_info": "0xed5e4ec1aa8bc8070bcb4ea9099151609900ca6fa2ee680f9e017162a2530bbe",
                "puzzle_hash": "0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a"
            },
            "puzzle_reveal": "0x80",
            "solution": "0x80"
        }
    ]
}
{
    "status": "SUCCESS",
    "success": true
}

>>> piggybank = get_coin("cfc5d753a6432d760df5c93748b7eed6e5a006664b98f48831c9e98746789666")
>>> contribution_300 = get_coin("66dc36a6dbe5a598e403821f43e38840fa67de0af28449537122498ad03e0efc")
>>> deposit(piggybank, contribution_300)
{
    "aggregated_signature": "0xc00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "coin_solutions": [
        {
            "coin": {
                "amount": 300,
                "parent_coin_info": "0x03e630b3f0f5aa28d208ec3c27be3ac4398c3757e2d8aa09a0dc907d8667db79",
                "puzzle_hash": "0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8"
            },
            "puzzle_reveal": "0xff02ffff01ff02ffff03ffff15ff0bff0580ffff01ff02ffff03ffff15ff0bff0e80ffff01ff04ffff04ff0affff04ff04ffff04ff0bff80808080ffff04ffff04ff0affff04ff17ffff01ff80808080ff808080ffff01ff04ffff04ff0affff04ff17ffff04ff0bff80808080ff808080ff0180ffff01ff088080ff0180ffff04ffff01ffa0a6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6ff338201f4ff018080",
            "solution": "0xff82012cff820258ffa0c23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f880"
        },
        {
            "coin": {
                "amount": 300,
                "parent_coin_info": "0x05ea529a7c9c3d4b67fea1449d977dbb4bc685686b232c8d32c499a39f5bc1c3",
                "puzzle_hash": "0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a"
            },
            "puzzle_reveal": "0x80",
            "solution": "0x80"
        }
    ]
}
{
    "status": "SUCCESS",
    "success": true
}
```

### checking the result

We should now see that all contribution coins were spent, new piggybank coin was created, and **600** mojo coin was sent to the cash-out wallet.

```sh
# all contributions were exhausted
❯ cdv rpc coinrecords --by puzhash 0x4bf5122f344554c53bde2ebb8cd2b7e3d1600ad631c385a5d7cce23c7785459a -ou -s 570135
[]

# new piggybank is created
❯ cdv rpc coinrecords --by puzhash 0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8 -ou -s 570135
[{'coin': {'amount': 0,
           'parent_coin_info': '0xcfc5d753a6432d760df5c93748b7eed6e5a006664b98f48831c9e98746789666',
           'puzzle_hash': '0xc23532ddfb0d78654cf73e9a1e5b417fc7cc110d40cb8c08198d6057064eb7f8'},
  'coinbase': False,
  'confirmed_block_index': 571381,
  'spent': False,
  'spent_block_index': 0,
  'timestamp': 1631282744}]

# cash-out puzzle hash
❯ cdv rpc coinrecords --by puzhash 0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6 -ou -s 570135
[{'coin': {'amount': 600,
           'parent_coin_info': '0xcfc5d753a6432d760df5c93748b7eed6e5a006664b98f48831c9e98746789666',
           'puzzle_hash': '0xa6a4ed372c785816fb92fb79b96fd7f9758811907f74ebe189c93310e3ba89e6'},
  'coinbase': False,
  'confirmed_block_index': 571381,
  'spent': False,
  'spent_block_index': 0,
  'timestamp': 1631282744}]

```
## Conclusions

Although it's good to understand the how things work behind the scenes, pratically, performing all steps manually is hard and very error-prone. With driver code, we are now able to automate all of the steps we need to deploy and spend smart coins.

> However, as we know, the smart coins we have are not secure because anyone can spend them with empty aggregated signature. Moreover, any malicious full node can modify our spend bundle and take all of our mojos! [Next post](POST-4.md) , let's try to secure our smart coins step by step.

## Files

- [piggybank_drivers.py](https://github.com/kimsk/chia-piggybank/blob/c8bdd9cc3eead4bac816ae0afd34e0358f834e6a/piggybank/piggybank_drivers.py)

## References

- [6 - Driver Code](https://www.youtube.com/watch?v=dGohmAc658c)
- [Chia-Network/chia-blockchain](https://github.dev/Chia-Network/chia-blockchain)
- [Chia-Network/chia-dev-tools](https://github.dev/Chia-Network/chia-dev-tools)
