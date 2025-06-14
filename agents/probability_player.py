from game.players import BasePokerPlayer
from copy import deepcopy
from itertools import combinations
from game.engine.card import Card
from game.engine.deck import Deck
from game.engine.hand_evaluator import HandEvaluator
import random
import math
from collections import Counter


class ProbabilityAgent(BasePokerPlayer):
    
    def declare_action(self, valid_actions, hole_card, round_state):
        
        if self.get_expected_stack_if_fold_all(round_state) > 1000:
            self.log("I will win this round, so I will fold.")
            return self.fold_action()
        
        my_hole_cards = [Card.from_str(c) for c in hole_card]
        community_cards = [Card.from_str(c) for c in round_state['community_card']]
        my_stack = next(player["stack"] for player in round_state["seats"] if player["uuid"] == self.uuid)
        pot_amount = round_state['pot']['main']['amount']
        call_action = valid_actions[1]
        raise_action = valid_actions[2]
        call_amount = call_action["amount"]
        min_raise = raise_action["amount"]["min"]
        # max_raise = raise_action["amount"]["max"]
        max_raise = self.compute_minimal_raise(round_state, valid_actions)
        street = round_state['street']
        
        # using preflop table
        # if street == "preflop" and len(round_state['action_histories']['preflop']) <= 3:
        #     hand_key = self.get_hand_key(my_hole_cards[0], my_hole_cards[1])
        #     if self.is_button(round_state):
        #         if hand_key in BUTTON_OPEN_RAISE_HANDS:
        #             self.log("SB Raise")
        #             return self.raise_action(min_raise, call_amount)
        #     elif self.is_big_blind(round_state):
        #         if hand_key in BB_3BET_HANDS:
        #             self.log("BB Raise")
        #             return self.raise_action(min_raise, call_amount)
        #         elif hand_key in BB_CALL_HANDS:
        #             self.log("BB Call")
        #             return self.call_action(call_amount)
        #     self.log(f"Preflop Hand Not Strong: {hand_key if hand_key else 'Unknown'}")
        #     return "fold", valid_actions[0]["amount"]


        pot_odds = call_amount / (pot_amount + call_amount) if (pot_amount + call_amount) > 0 else 0
        win_rate = self.estimate_win_rate(my_hole_cards, community_cards, num_simulations=2000)
        
        self.log(f"Win Rate: {win_rate:.2f}, Pot Odds: {pot_odds:.2f}, Call Amount: {call_amount}, Min Raise: {min_raise}, Max Raise: {max_raise}, Pot Amount: {pot_amount}")
        
        # Bluff
        # if street == "river" and my_stack < 1000:
        #     if win_rate < 0.2 and self.has_blocker(my_hole_cards, community_cards):
        #         self.log("Bluff")
        #         return self.raise_action(raise_action["amount"]["max"], call_amount)
        #     if win_rate < 0.2:
        #         self.log("Has No Blocker")
            

        best_ev = -float("inf")
        best_action = self.fold_action()

        current_stack = my_stack
        sunk_cost = max([a["amount"] for a in round_state["action_histories"].get(street, []) if a["uuid"] == self.uuid], default=0)

        # --- Fold EV ---
        ev_fold = current_stack
        if ev_fold > best_ev:
            best_ev = ev_fold
            best_action = self.fold_action()

        # --- Call EV ---
        ev_call = (
            win_rate * (current_stack + pot_amount) +
            (1 - win_rate) * (current_stack - call_amount)
        )
        if ev_call > best_ev:
            best_ev = ev_call
            best_action = self.call_action(call_amount)

        # --- Raise EV (try multiple raise sizes) ---
        steps = 2

        if max_raise > 0 and max_raise >= min_raise:
            for raise_amt in range(min_raise, max_raise + 1, max(1, (max_raise - min_raise) // steps)):
                our_cost = raise_amt - sunk_cost
                opp_call_amt = raise_amt - call_amount  # 假設對手 call 滿額

                ev_raise = (
                    win_rate * (current_stack + pot_amount + opp_call_amt) +
                    (1 - win_rate) * (current_stack - our_cost)
                )

                if ev_raise > best_ev:
                    best_ev = ev_raise
                    best_action = self.raise_action(raise_amt, call_amount)
                        
        return best_action
        

        # if win_rate >= 0.8 and max_raise > 0:
        #     return self.raise_action(max_raise, call_amount)
        # if win_rate >= 0.75 and min_raise > 0:
        #     return self.raise_action(min(min_raise + 100, max_raise), call_amount)
        # if win_rate >= 0.7 and min_raise > 0:
        #     return self.raise_action(min(min_raise + 50, max_raise), call_amount)
        # if win_rate >= 0.65 and min_raise > 0:
        #     return self.raise_action(min_raise, call_amount)
        
        # if win_rate > pot_odds:
        #     return self.call_action(call_amount)
        # return self.fold_action()

    def receive_game_start_message(self, game_info):
        pass
    
    def receive_round_start_message(self, round_count :int , hole_card : list, seats : list):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass
    
    def receive_round_result_message(self, winners, hand_info, round_state):
        pass
    
    def estimate_win_rate(self, my_hole_cards, community_cards, num_simulations=2000):
        win = 0

        for _ in range(num_simulations):
            # 建立一副新的牌，移除已知的牌
            deck = Deck()
            known_cards = my_hole_cards + community_cards
            deck.deck = [card for card in deck.deck if card not in known_cards]
            deck.shuffle()

            # 抽對手手牌與剩下的 community cards
            opponent_hole = deck.draw_cards(2)
            community_fill = 5 - len(community_cards)
            full_community = community_cards + deck.draw_cards(community_fill)

            # 評估雙方手牌強度
            my_score = HandEvaluator.eval_hand(my_hole_cards, full_community)
            opponent_score = HandEvaluator.eval_hand(opponent_hole, full_community)
            
            assert my_score is not None, "My hand evaluation failed"
            assert opponent_score is not None, "Opponent hand evaluation failed"

            if my_score > opponent_score:
                win += 1
        return win / num_simulations
    
    def get_expected_stack_if_fold_all(self, round_state):
        max_raiseound = 20
        current_round = round_state["round_count"]
        remaining_rounds = max_raiseound - current_round + 1

        my_stack = next(player["stack"] for player in round_state["seats"] if player["uuid"] == self.uuid)

        small = round_state["small_blind_amount"]
        big = small * 2

        my_pos = next(i for i, p in enumerate(round_state["seats"]) if p["uuid"] == self.uuid)
        small_blind_times = (remaining_rounds + (my_pos == round_state["small_blind_pos"])) // 2
        big_blind_times = remaining_rounds - small_blind_times

        total_loss = small * small_blind_times + big * big_blind_times
        return my_stack - total_loss

    def compute_minimal_raise(self, round_state, valid_actions):
        # opp_stack = next(player["stack"] for player in round_state["seats"] if player["uuid"] != self.uuid)
        my_stack_after_fold = self.get_expected_stack_if_fold_all(round_state)
        if my_stack_after_fold > 1000:
            return -1

        raise_needed = 1001 - my_stack_after_fold
        raise_action = valid_actions[2]
        min_raise = raise_action["amount"]["min"]
        max_raise = raise_action["amount"]["max"]

        return min(max_raise, max(min_raise, raise_needed))

    def has_flush_blocker(self, hole_cards, board_cards):
        board_suits = [card.suit for card in board_cards]
        suit_counts = Counter(board_suits)

        # 找出最可能成為 flush 的花色
        for suit, count in suit_counts.items():
            if count >= 3:
                # 你是否持有這個花色
                return any(card.suit == suit for card in hole_cards)
        return False        

    def has_straight_blocker(self, hole_cards, board_cards):
        # RANK_ORDER = "23456789TJQKA"
        # rank_to_index = {r: i for i, r in enumerate(RANK_ORDER)}
        
        # all_cards = hole_cards + board_cards
        # rank_indexes = set(rank_to_index[card.rank] for card in all_cards)

        # 找出 board 上的 rank
        board_rank_indexes = set(card.rank for card in board_cards)
        hole_rank_indexes = set(card.rank for card in hole_cards)

        # 嘗試找可能出現順子的區間
        for start in range(0, 9):  # 最長為 A=12，所以 12-4=8
            straight_indexes = set(range(start, start + 5))
            overlap = board_rank_indexes & straight_indexes

            if len(overlap) == 4:
                # 你是否有缺的那一張
                needed = straight_indexes - board_rank_indexes
                if hole_rank_indexes & needed:
                    return True
        return False
    
    def has_set_blocker(self, hole_cards, board_cards):
        board_ranks = [card.rank for card in board_cards]
        paired_ranks = [r for r in set(board_ranks) if board_ranks.count(r) >= 2]
        return any(c.rank in paired_ranks for c in hole_cards)

    def has_overpair_blocker(self, hole_cards, board_cards):
        board_ranks = [c.rank for c in board_cards]
        max_board_rank = max(board_ranks)

        return any(
            c.rank > max_board_rank
            for c in hole_cards
        )
    def has_top_pair_blocker(self, hole_cards, board_cards):
        board_ranks = [c.rank for c in board_cards]
        top_rank = max(board_ranks)

        return any(c.rank == top_rank for c in hole_cards)

    def has_blocker(self, hole_cards, board_cards):
        blocker = False
        try :
            blocker = self.has_flush_blocker(hole_cards, board_cards) if blocker == False else True
            # self.log("Have Flush Blocker")
        except Exception as e:
            print(f"ERROR IN FLUSH BLOCKER : {e}")
        try :
            blocker = self.has_straight_blocker(hole_cards, board_cards) if blocker == False else True
            # self.log("Have Straight Blocker")
        except Exception as e:
            print(f"ERROR IN STRAIGHT BLOCKER : {e}")
        try :
            blocker = self.has_set_blocker(hole_cards, board_cards) if blocker == False else True
            # self.log("Have Set Blocker")
        except Exception as e:
            print(f"ERROR IN SET BLOCKER : {e}")
        try :
            blocker = self.has_overpair_blocker(hole_cards, board_cards) if blocker == False else True
            # self.log("Have Overpair Blocker")
        except Exception as e:
            print(f"ERROR IN OVERPAIR BLOCKER : {e}")
        try :
            blocker = self.has_top_pair_blocker(hole_cards, board_cards) if blocker == False else True
            # self.log("Have Top Pair Blocker")
        except Exception as e:
            print(f"ERROR IN TOP PAIR BLOCKER : {e}")
            
        return blocker



    def log(self, message):
        print("=" * 50)
        print(f"[MonteCarlo Agent] {message}")
        print("=" * 50)
        
    def get_hand_key(self, card1, card2):
        rank_order = "23456789TJQKA"
        r1, r2 = Card.RANK_MAP[card1.rank], Card.RANK_MAP[card2.rank]
        s1, s2 = card1.suit, card2.suit
        suited = s1 == s2

        ranks = sorted([r1, r2], key=lambda r: rank_order.index(r), reverse=True)
        if ranks[0] == ranks[1]:
            return ranks[0] + ranks[1]  # Pair
        return ranks[0] + ranks[1] + ("s" if suited else "o")
    
    def is_button(self, round_state):
        button_index = round_state["small_blind_pos"]
        button_uuid = round_state["seats"][button_index]["uuid"]
        return self.uuid == button_uuid
    
    def is_big_blind(self, round_state):
        bb_index = round_state["big_blind_pos"]
        return round_state["seats"][bb_index]["uuid"] == self.uuid
    
    def is_first_to_act(self, round_state):
        next_index = round_state["next_player"]
        return round_state["seats"][next_index]["uuid"] == self.uuid

    def raise_action(self, raise_amount, call_amount):
        if raise_amount > 0:
            # self.log(f"Raise {raise_amount}")
            return "raise", raise_amount
        return self.call_action(call_amount)
    
    def call_action(self, call_amount):
        if call_amount >= 0:
            # self.log(f"Call {call_amount}")
            return "call", call_amount
        return self.fold_action()
    
    def fold_action(self):
        # self.log("Fold")
        return "fold", 0




    
        
        
def setup_ai():
    return ProbabilityAgent()


BUTTON_OPEN_RAISE_HANDS = {
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
    "KQs", "KJs", "KTs", "K9s", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
    "QJs", "QTs", "Q9s", "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s",
    "JTs", "J9s", "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s",
    "T9s", "T8s", "T7s", "T6s", "T5s", "T4s", "T3s", "T2s",
    "98s", "97s", "96s", "95s", "94s", "93s", "92s",
    "87s", "86s", "85s", "84s", "83s", "82s",
    "76s", "75s", "74s", "73s", "72s",
    "65s", "64s", "63s", "62s",
    "54s", "53s", "52s",
    "43s", "42s",
    "32s",

    "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o", "A6o", "A5o", "A4o", "A3o", "A2o",
    "KQo", "KJo", "KTo", "K9o", "K8o", "K7o", "K6o", "K5o",
    "QJo", "QTo", "Q9o", "Q8o", "Q7o", "Q6o",
    "JTo", "J9o", "J8o", "J7o", "J6o",
    "T9o", "T8o", "T7o", "T6o",
    "98o", "97o", "96o",
    "87o", "86o",
    "76o", "75o",
    "65o", 
    "54o",
}

BB_3BET_HANDS = {
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
    "KQs", "KJs", "KTs", "K9s",
    "QJs", "QTs", "Q9s",
    "JTs", "J9s",
    "T9s",
    "98s",
    "87s",
    "76s", 
    "65s",
    
    "AKo", "AQo", "AJo", "ATo", "A9o", "A8o",
    "KQo", "KJo", "KTo",
    "QJo", "QTo",
    "JTo",
    "T9o",
}

BB_CALL_HANDS = {
    "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s",
    "Q8s", "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s",
    "J8s", "J7s", "J6s", "J5s", "J4s", "J3s", "J2s",
    "T8s", "T7s", "T6s", "T5s", "T4s", "T3s", "T2s",
    "97s", "96s", "95s", "94s", "93s", "92s",
    "86s", "85s", "84s", "83s", "82s",
    "75s", "74s", "73s", "72s",
    "64s", "63s", "62s",
    "54s", "53s", "52s",
    "43s", "42s",
    "32s",
}