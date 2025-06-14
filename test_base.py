import json
from collections import defaultdict
from agents.probability_player import setup_ai as probability_ai
from agents.decision_player import setup_ai as decision_ai
from check_base import CheckBaseline, BASELINES
import argparse


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-b')
    parser.add_argument('-m')
    
    args = parser.parse_args()

    idx = int(args.b)
    print([BASELINES[idx]])

    checker = CheckBaseline([BASELINES[idx]]) # test baseline idx
    
    if idx == 0:
        checker = CheckBaseline(BASELINES) # test all baselines (1~7)
        
    if args.m == "p" :
        checker.run_distribution(probability_ai, runs=10, output_file="monte_carlo_score_distribution.json")
    elif args.m == "d":
        checker.run_distribution(decision_ai, runs=10, output_file="monte_carlo_score_distribution.json")
    else :
        print("model not defined")
        