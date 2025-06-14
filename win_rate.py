import matplotlib.pyplot as plt
import numpy as np
from game.engine.card import Card
from game.engine.deck import Deck
from game.engine.hand_evaluator import HandEvaluator

def estimate_win_rate(hole_cards, community_cards=[], num_simulations=1000):
    win = 0
    for _ in range(num_simulations):
        deck = Deck()
        known = hole_cards + community_cards
        deck.deck = [card for card in deck.deck if card not in known]
        deck.shuffle()

        opp_hole = deck.draw_cards(2)
        community_fill = 5 - len(community_cards)
        full_community = community_cards + deck.draw_cards(community_fill)

        my_score = HandEvaluator.eval_hand(hole_cards, full_community)
        opp_score = HandEvaluator.eval_hand(opp_hole, full_community)

        assert my_score is not None, "My hand evaluation failed"
        assert opp_score is not None, "Opponent hand evaluation failed"

        if my_score > opp_score:
            win += 1
    return win / num_simulations


def sample_winrates(num_samples=10, num_simulations_per_hand=1000):
    winrates = []
    seen_hands = set()

    while len(winrates) < num_samples:
        deck = Deck()
        deck.shuffle()
        hole_cards = deck.draw_cards(2)
        key = tuple(sorted(str(c) for c in hole_cards))
        if key in seen_hands:
            continue
        seen_hands.add(key)

        winrate = estimate_win_rate(hole_cards, community_cards=[], num_simulations=num_simulations_per_hand)
        winrates.append(winrate)

    return winrates


# 抽樣並繪圖
winrates = sample_winrates(num_samples=1000, num_simulations_per_hand=1000)
mean = np.mean(winrates)
std = np.std(winrates)

plt.figure(figsize=(10, 6))
plt.hist(winrates, bins=20, edgecolor='black', alpha=0.7)
plt.axvline(mean, color='red', linestyle='dashed', linewidth=2, label=f'Mean = {mean:.2f}')
plt.axvline(mean - std, color='blue', linestyle='dotted', linewidth=1, label=f'Std Dev = {std:.2f}')
plt.axvline(mean + std, color='blue', linestyle='dotted', linewidth=1)

plt.xlabel('Estimated Win Rate')
plt.ylabel('Frequency')
plt.title('Preflop Win Rate Distribution')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('preflop_win_rate_distribution.png')
plt.show()
