import json
from game.game import setup_config, start_poker
from agents.call_player import setup_ai as call_ai
from agents.random_player import setup_ai as random_ai
from agents.console_player import setup_ai as console_ai
from game.engine.deck import Deck

config = setup_config(max_round=1, initial_stack=1000, small_blind_amount=5)
config.register_player(name="p1", algorithm=console_ai())
config.register_player(name="p2", algorithm=console_ai())

# Prepare a cheat deck for debugging
# cheat_card_ids = [7, 6, 20, 3, 8, 35, 26, 34, 48] # evenly distributed case 1
# cheat_card_ids = [35, 43, 17, 12, 3, 33, 26, 19, 31] # evenly distributed case 2
cheat_card_ids = [14, 4, 6, 19, 28, 31, 3, 44, 24] # straight wheel
cheat_deck = Deck(cheat=True, cheat_card_ids=cheat_card_ids)

# Pass the deck as a list (one per round)
game_result = start_poker(config, verbose=1, decks=[cheat_deck])

print(json.dumps(game_result, indent=4))