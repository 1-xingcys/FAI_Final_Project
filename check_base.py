import json
from collections import defaultdict
import matplotlib.pyplot as plt
from game.game import setup_config, start_poker
from agents.probability_player import setup_ai as probability_ai


from baseline0 import setup_ai as baseline0_ai
from baseline1 import setup_ai as baseline1_ai
from baseline2 import setup_ai as baseline2_ai
from baseline3 import setup_ai as baseline3_ai
from baseline4 import setup_ai as baseline4_ai
from baseline5 import setup_ai as baseline5_ai
from baseline6 import setup_ai as baseline6_ai
from baseline7 import setup_ai as baseline7_ai

class CheckBaseline:
    def __init__(self, baselines, max_round=20, initial_stack=1000, small_blind_amount=5):
        self.baselines = baselines
        self.ai_name = "me"
        self.max_round = max_round
        self.initial_stack = initial_stack
        self.small_blind_amount = small_blind_amount
    
    def BO5(self, baseline, agent, num_games=5):
        win_count = 0
        final_stacks = []
        for _ in range(num_games):
            config = setup_config(
                max_round=self.max_round,
                initial_stack=self.initial_stack,
                small_blind_amount=self.small_blind_amount
            )
            config.register_player(name=f"{baseline['name']}", algorithm=baseline["setup_ai"]())
            config.register_player(name=self.ai_name, algorithm=agent())
            game_result = start_poker(config, verbose=2)
            for player_info in game_result["players"]:
                print(f"{player_info['name']} stack: {player_info['stack']}")
                if player_info["name"] == self.ai_name:
                    win_count += 1 if player_info["stack"] > 1000 else 0
                    final_stacks.append(player_info["stack"])
                    
        # Compute Score
        final_stacks.sort(reverse=True)
        print(f"Final Stacks : {final_stacks}")
        score = 0
        if win_count >= 3:
            score = 5
        else : 
            for stack in final_stacks[0:2]:
                if stack > 1000:
                    score += 1.5
                elif stack >= 500:
                    score += round(stack / 1000, 1)  
        return {"win_rate" : win_count / num_games, "score" : score}

    def run(self, agent, output_file="baseline_results.json"):
        results = {}
        total_score = 0
        for baseline in self.baselines:
            results[baseline["name"]] = self.BO5(baseline, agent)
            total_score += results[baseline["name"]]["score"]
        for baseline in self.baselines:
            print(f"{baseline['name']} win rate: {results[baseline['name']]['win_rate'] * 100:.2f}%, Get {results[baseline['name']]['score']}")
        print(f"Final Score = {total_score} / 35")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=4)
    
    def run_distribution(self, agent, runs, output_file="score_distribution.json"):
        baseline_score_history = defaultdict(list)
        baseline_win_rate_history = defaultdict(list)

        for i in range(runs):
            for baseline in self.baselines:
                result = self.BO5(baseline, agent)
                baseline_score_history[baseline["name"]].append(result["score"])
                baseline_win_rate_history[baseline["name"]].append(result["win_rate"])
        
        # Print summary
        for name, scores in baseline_score_history.items():
            avg = sum(scores) / len(scores)
            print(f"{name}: avg score = {avg:.2f}, min = {min(scores)}, max = {max(scores)}")
        for name, win_rates in baseline_win_rate_history.items():
            avg = sum(win_rates) / len(win_rates)
            print(f"{name}: win rate = {avg}, min = {min(win_rates)}, max = {max(win_rates)}")

        # Save to file
        with open(output_file, "w") as f:
            json.dump(baseline_score_history, f, indent=4)
        
        return baseline_score_history

BASELINES = [
        {"name": "baseline0", "setup_ai": baseline0_ai},
        {"name": "baseline1", "setup_ai": baseline1_ai},
        {"name": "baseline2", "setup_ai": baseline2_ai},    
        {"name": "baseline3", "setup_ai": baseline3_ai},
        {"name": "baseline4", "setup_ai": baseline4_ai},
        {"name": "baseline5", "setup_ai": baseline5_ai},
        {"name": "baseline6", "setup_ai": baseline6_ai},
        {"name": "baseline7", "setup_ai": baseline7_ai},
    ]


    
# checker = CheckBaseline(    baselines=[
#         # {"name": "baseline0", "setup_ai": baseline0_ai},
#         {"name": "baseline1", "setup_ai": baseline1_ai},
#         # {"name": "baseline2", "setup_ai": baseline2_ai},    
#         # {"name": "baseline3", "setup_ai": baseline3_ai},
#         # {"name": "baseline4", "setup_ai": baseline4_ai},
#         # {"name": "baseline5", "setup_ai": baseline5_ai},
#         # {"name": "baseline6", "setup_ai": baseline6_ai},
#         # {"name": "baseline7", "setup_ai": baseline7_ai},
#         # {"name" : "randomPlayer", "setup_ai": random_ai},
#         # {"name" : "callPlayer", "setup_ai": call_ai},
#         # {"name" : "AllinPlayer", "setup_ai": allin_ai}
#     ]
# )


if __name__ == "__main__":
    pass
    # print("FUCK")
    # checker.run(allin_ai, output_file="allin_vs_baseline.json")
    # checker.run(probability_ai, output_file="monte_carlo_vs_baseline.json")
    # score_history = checker.run_distribution(probability_ai, runs=5, output_file="monte_carlo_score_distribution.json")