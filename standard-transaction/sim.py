import asyncio

from cdv.test import Network, Wallet

from chia.types.blockchain_format.program import Program
from chia.types.spend_bundle import SpendBundle

network: Network = asyncio.run(Network.create())
asyncio.run(network.farm_block())

alice: Wallet = network.make_wallet("alice")
print(f'alice pk:\t{alice.pk()}')
bob: Wallet = network.make_wallet("bob")
print(f'bob pk:\t\t{bob.pk()}')
charlie: Wallet = network.make_wallet("charlie")
print(f'charlie pk:\t{charlie.pk()}')


def farm(farmer: Wallet):
    print(f'alice balance:\t{alice.balance()}')
    asyncio.run(network.farm_block(farmer=farmer))
    print(f'alice balance:\t{alice.balance()}')

def get_coin(wallet: Wallet, amt, fee=0):
    return asyncio.run(alice.choose_coin(amt + fee))

def push_tx(spend_bundle: SpendBundle):
    result = asyncio.run(network.push_tx(spend_bundle))
    return result

def launch_smart_coin(wallet: Wallet, puzzle: Program, amt):
    return asyncio.run(wallet.launch_smart_coin(puzzle, amt=amt))

def end():
    asyncio.run(network.close())