import json
from game.game import setup_config, start_poker
from agents.call_player import setup_ai as call_ai
from agents.random_player import setup_ai as random_ai
from agents.console_player import setup_ai as console_ai
from agents.probability_player import setup_ai as monte_carlo_ai
from agents.Allin_player import setup_ai as allin_ai
# from baseline0 import setup_ai as baseline0_ai


cnt = 0
for _ in range(30):

    config = setup_config(max_round=20, initial_stack=1000, small_blind_amount=5)
    # config.register_player(name="p1", algorithm=baseline0_ai())
    config.register_player(name="p2", algorithm=random_ai())
    config.register_player(name="me", algorithm=allin_ai())
    # config.register_player(name="me", algorithm=test_ai())

    ## Play in interactive mode if uncomment
    #config.register_player(name="me", algorithm=console_ai())
    game_result = start_poker(config, verbose=1)
    cnt += 1 if game_result["players"][1]["stack"] > 1000 else 0

print(f"AI win rate: {cnt / 30 * 100:.2f}%")
