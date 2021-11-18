# Aggregated Signature

So far, in all of our spend bundles, we have been using an empty signature, `0xc00000000000000000000000000...`, to simplify our learning. However, this lets any (malicious or not) farmers to be able to modify our `coin_solutions` (especially the `solution`) inside the spend bundles. 

## Stealing Dummy Coin

Let's look at our dummy coin's puzzle again:
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

The puzzle hash is `b92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd`. Anyone can looks at the dummy coins that were spent and see the `puzzle_reveal` and `solution` associated with those spends.

With the PowerShell script below, we could see the puzzle and all solutions associated with those spent coins.
```PowerShell
function Get-Spend-Bundles
{
    param($Puzzle_Hash)
    $coins =
        cdv rpc coinrecords --by puzhash $Puzzle_Hash -nd
        | ConvertFrom-Json -AsHashtable
    $spent_coins =
        $coins.GetEnumerator()
        | Where-Object { $_.Value.spent }
    
    $blokspends = $spent_coins
    | ForEach-Object { 
        cdv rpc blockspends --coinid $_.Name --block-height $_.Value.spent_block_index
        | ConvertFrom-Json
    }

    $blokspends
}

$blockspends = Get-Spend-Bundles -Puzzle_Hash b92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd
cdv clsp disassemble $blockspends[0].puzzle_reveal
$blockspends | % { cdv clsp disassemble $_.solution }
```

```lisp
(a (q 4 (c 2 (c 11 (c 5 ()))) ()) (c (q . 51) 1))
(299 0xb92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd)
(101 0xbe880f244f25c30cca4f30ec8bb90fef4ec88d612ceaa57ea027ba3a7bf0cc32)
(100 0xb92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd)
(100 0xb92a9d42c0f3e3612e98e1ae7b030ed425e076eda6238c7df3c481bf13de3bfd)
(100 0xc363c01fea7794ea86c0801bf4ae8f210e3be0361dd0570b6ad185087367ce53)
```

It's easy to see that there was no condition in the output that do assertion.

## Creating A Signature

To prevent our spend to be modified by any malicious farmer, we have to sign our spend with our private/secret key. If anything in the spend bundle has been tampered, the signature will be invalid which makes the spend bundle invalid.

Let see some samples of signing and verifying the message:

```sh
# generate a random set of keys
❯ $key = cdv inspect keys --random; $key[0]; $key[1]

Secret Key: 71005b4be2f8a24427dbdcaaae48cab31fa86afc0fe73c40b88b0841f40e4c4d
Public Key: 9688d47b019c2bda4228cae785b2ccd5bf0933b45aa6c355a45323f848f7c1cdd80605ee27f4b8d4b8e379c959f639f3

# sign a message with a private key
❯ cdv inspect signatures --secret-key "71005b4be2f8a24427dbdcaaae48cab31fa86afc0fe73c40b88b0841f40e4c4d" --utf-8 "hello chia"
a63edc8f27e6f78f01317b7c7714be6b3e59e9d237d4e2f63af832efff71dfc87038df5a52201374cd082a6cd73a80f20594e4f11a74a5d90f0ad9d5b6f02b97b7cdce496158c951e250b02afb46b0b3ee5b9a97035f0b629f80399d86e700e8

# verify the message and signature with a public key
❯ chia keys verify --message "hello chia" --public_key "9688d47b019c2bda4228cae785b2ccd5bf0933b45aa6c355a45323f848f7c1cdd80605ee27f4b8d4b8e379c959f639f3" --signature "a63edc8f27e6f78f01317b7c7714be6b3e59e9d237d4e2f63af832efff71dfc87038df5a52201374cd082a6cd73a80f20594e4f11a74a5d90f0ad9d5b6f02b97b7cdce496158c951e250b02afb46b0b3ee5b9a97035f0b629f80399d86e700e8"
True
```
## Aggregated Signature

[In Chia, we use BLS Signatures to sign any relevant data.](https://chialisp.com/docs/coins_spends_and_wallets#bls-aggregated-signatures). BLS allows you to compress the multiple signatures into a single signature called **aggregated signature**. In addition , BLS signature can aggregate public keys into a single key that will verify their aggregated signatures. The obvious benefit or aggregated signature is that it supports multisig without using a lot of space.

Let's see how can we create and verify an aggregated signature:

```sh
# generate three random keys and use them in our python code
❯ cdv inspect keys --random;
Secret Key: 0a900677882bcfa970724a381900e7b6c0d40425fda8a2d1f2db90a13d960472
Public Key: a4d7da9a1c5210352e4487abc45cc09ca7e523630740e208087c4eb5f0c7ea85819c7affae1b1c846feabf49b071ad1d
...

❯ cdv inspect keys --random;
Secret Key: 0f90b1a9ca144b969283a989eb8c5273cbe192df58eb79e551ed538759f9ee14
Public Key: a4a0b8aed35ad944b287d0a46245c0bc66e1b0ae21cfa0190d90f2dc0a16b0482c44ad5f8b7256357d4f108d4ed5a9d1
...

❯ cdv inspect keys --random;
Secret Key: 12acd472632e04bf69ff6bf9715e37fdd8d752874e29ae44ba8d53bb3744b4fc
Public Key: a4d62928c171673d15f268812499870346e7ce2d78321a23fc9584ea3c21f090a84215cc522a15de967a96aaae710587
...
```

```python
from blspy import (PrivateKey, BasicSchemeMPL,
                   G1Element, G2Element)

sk1: PrivateKey = PrivateKey.from_bytes(bytes.fromhex("0a900677882bcfa970724a381900e7b6c0d40425fda8a2d1f2db90a13d960472"))
pk1: G1Element = sk1.get_g1()
assert pk1 == G1Element.from_bytes(bytes.fromhex("a4d7da9a1c5210352e4487abc45cc09ca7e523630740e208087c4eb5f0c7ea85819c7affae1b1c846feabf49b071ad1d"))
sk2: PrivateKey = PrivateKey.from_bytes(bytes.fromhex("0f90b1a9ca144b969283a989eb8c5273cbe192df58eb79e551ed538759f9ee14"))
pk2: G1Element = sk2.get_g1()
assert pk2 == G1Element.from_bytes(bytes.fromhex("a4a0b8aed35ad944b287d0a46245c0bc66e1b0ae21cfa0190d90f2dc0a16b0482c44ad5f8b7256357d4f108d4ed5a9d1"))
sk3: PrivateKey = PrivateKey.from_bytes(bytes.fromhex("12acd472632e04bf69ff6bf9715e37fdd8d752874e29ae44ba8d53bb3744b4fc"))
pk3: G1Element = sk3.get_g1()
assert pk3 == G1Element.from_bytes(bytes.fromhex(" a4d62928c171673d15f268812499870346e7ce2d78321a23fc9584ea3c21f090a84215cc522a15de967a96aaae710587"))

# a message is signed with three different private keys to get three signatures
message = "hello chia"
message_as_bytes = bytes(message, "utf-8")
sig1: G2Element = BasicSchemeMPL.sign(sk1, message_as_bytes)
sig2: G2Element = BasicSchemeMPL.sign(sk2, message_as_bytes)
sig3: G2Element = BasicSchemeMPL.sign(sk3, message_as_bytes)

# verify signatures
verify1 = BasicSchemeMPL.verify(pk1, message_as_bytes, sig1)
verify2 = BasicSchemeMPL.verify(pk2, message_as_bytes, sig2)
verify3 = BasicSchemeMPL.verify(pk3, message_as_bytes, sig3)

# aggregate three signatures to one
agg_sig = BasicSchemeMPL.aggregate([sig1, sig2, sig3])

# aggregate three public keys to one aggregated public key
agg_pk = pk1 + pk2 + pk3
agg_verify = BasicSchemeMPL.verify(agg_pk, message_as_bytes, agg_sig)

print(agg_pk)

assert(verify1)
assert(verify2)
assert(verify3)
assert(agg_verify)
```

## AGG_SIG_UNSAFE

## AGG_SIG_ME

## References

- [chialisp.com | 2 - Coins, Spends and Wallets](https://chialisp.com/docs/coins_spends_and_wallets#bls-aggregated-signatures)
- [chialsip.com | 8 - Security](https://chialisp.com/docs/security)
- [tutorial | 4 - Securing a Smart Coin](https://youtu.be/_SBGfMZhRd8)
- [High Level Tips 1 - Managing State, Coin Creation, Announcements](https://www.youtube.com/watch?v=lDXB4NlbQ-E)
- [High Level Tips 2 - Security, Checking Arguments & Signatures](https://www.youtube.com/watch?v=T4noZyNJkFA)
- [What are BLS Signatures?](https://aggsig.me/signatures.html)
- [BLS Signatures](https://www.marigold.dev/post/bls-signatures)
- [Difference between shamir secret sharing (SSS) vs Multisig vs aggregated signatures (BLS) vs distributed key generation (dkg) vs threshold signatures](https://www.cryptologie.net/article/486/difference-between-shamir-secret-sharing-sss-vs-multisig-vs-aggregated-signatures-bls-vs-distributed-key-generation-dkg-vs-threshold-signatures/)