from cdv.util.load_clvm import load_clvm
from chia.types.blockchain_format.program import Program


from sim import alice, bob, farm, get_coin, launch_smart_coin, push_tx, end
from utils import print_json
farm(alice)

hidden = load_clvm(
    "test_hidden.clsp", package_or_requirement=__name__, search_paths=["../include"]
) 
main = load_clvm(
    "test_main.clsp", package_or_requirement=__name__, search_paths=["../include"]
)

print(hidden)
print(main)

solution = Program.to([hidden, [1, 2]])
print(solution)
result = main.run(solution)
print(result)
main_curried = main.curry(hidden)
print(main_curried)
result = main_curried.run(Program.to([[1,2]]))
print(result)

end()