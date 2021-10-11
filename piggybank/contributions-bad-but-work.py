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
print_json(spend_bundle.to_json_dict())

# python3 ./contributions-bad.py > ../spend_bundles/contributions-bad.json