import random

import itertools
import operator

from collections import namedtuple

from isolation import Board
from sample_players import (RandomPlayer, open_move_score, improved_score, center_score)
from game_agent import (MinimaxPlayer, AlphaBetaPlayer)

from tournament import play_matches as tournament_play_matches

NUM_MATCHES = 5  # number of matches against each opponent
TIME_LIMIT = 150  # number of milliseconds before timeout

Agent = namedtuple("Agent", ["player", "name"])

def generate_score_function(a, b):
    def score(game, player):
        if game.is_loser(player):
            return float("-inf")

        if game.is_winner(player):
            return float("inf")

        opponent  = game.get_opponent(player)

        own_moves = game.get_legal_moves(player)
        opp_moves = game.get_legal_moves(opponent)

        own_count = float(len(own_moves))
        opp_count = float(len(opp_moves))
        count_ratio = own_count / (opp_count + 1)

        w, h = game.width, game.height
        y, x = game.get_player_location(player)
        center_distance = float((h - y)**2 + (w - x)**2)

        return (a * count_ratio) + (b * center_distance)

    return score

def play_round(cpu_agent, test_agents, win_counts, num_matches):
    timeout_count = 0
    forfeit_count = 0

    for _ in range(num_matches):

        games = sum([[Board(cpu_agent.player, agent.player),
                      Board(agent.player, cpu_agent.player)]
                    for agent in test_agents], [])

        # initialize all games with a random move and response
        for _ in range(2):
            move = random.choice(games[0].get_legal_moves())
            for game in games:
                game.apply_move(move)

        # play all games and tally the results
        for game in games:
            winner, _, termination = game.play(time_limit=TIME_LIMIT)
            win_counts[winner] += 1

def update(total_wins, wins):
    for player in total_wins:
        total_wins[player] += wins[player]
    return total_wins

def play_matches(cpu_agents, test_agents, num_matches):
    total_wins = {agent.player: 0 for agent in test_agents}
    total_matches = 2 * num_matches * len(cpu_agents)

    for idx, agent in enumerate(cpu_agents):
        wins = dict([ (a.player, 0) for a in test_agents ] + [ (agent.player, 0) ])

        play_round(agent, test_agents, wins, num_matches)
        total_wins = update(total_wins, wins)
        _total = 2 * num_matches
        round_totals = sum([[wins[agent.player], _total - wins[agent.player]] for agent in test_agents], [])

    return dict([ (a, 100. * total_wins[a.player] / total_matches) for a in test_agents])

def twiddle(fitness):

    step = 0.1
    threshold = 0.01
    max_iterations = 1000

    param_count = fitness.__code__.co_argcount
    param_delta = [  1.0 for _ in range(param_count) ]
    param_value = [ step for _ in range(param_count) ]

    param_stack = []

    # Initialize baseline error
    best_error = fitness(*param_value)

    for iteration in range(max_iterations):

        if sum(param_delta) <= threshold:
            break

        for i in range(param_count):
            param_test = param_value
            value = param_value[i]
            delta = param_delta[i]

            param_test[i] = value + delta
            fitness_error = fitness(*param_test)

            if fitness_error < best_error:
                best_error = fitness_error
                param_value[i] = param_test[i]
                param_delta[i] *= 1 + step
                continue

            param_test[i] = value - delta
            fitness_error = fitness(*param_test)

            if fitness_error < best_error:
                best_error = fitness_error
                param_value[i] = param_test[i]
                param_delta[i] *= 1 + step
                continue

            param_delta[i] *= 1 - step

        # Push new (better) param copy on stack
        pair = (best_error, list(param_value))
        param_stack.append(pair)

        best_fitness = 100. / max(best_error, 1)

        print(">>>>>>>>>>> twiddle:", iteration)
        print("param_value:", param_value)
        print("param_delta:", param_delta)
        print("best_error:", best_error)
        print("best_fitness:", best_fitness)
        print("-------------------------")

    # Sort stack with best_error values last
    param_stack.sort(key=operator.itemgetter(0), reverse=True)

    return param_stack

def optimize():

    cpu_agents = [
        Agent(RandomPlayer(), "Random"),
        Agent(MinimaxPlayer(score_fn=open_move_score), "MM_Open"),
        Agent(MinimaxPlayer(score_fn=center_score), "MM_Center"),
        Agent(MinimaxPlayer(score_fn=improved_score), "MM_Improved"),
        Agent(AlphaBetaPlayer(score_fn=open_move_score), "AB_Open"),
        Agent(AlphaBetaPlayer(score_fn=center_score), "AB_Center"),
        Agent(AlphaBetaPlayer(score_fn=improved_score), "AB_Improved")
    ]

    def fitness(a, b):
        score_func = generate_score_function(a, b)
        test_agent = Agent(AlphaBetaPlayer(score_fn=score_func), "AB_Custom")

        results = play_matches(cpu_agents, [ test_agent ], NUM_MATCHES)

        win_ratio = results[test_agent]
        error = 100. / win_ratio

        return error

    param_stack = twiddle(fitness)

    _, best_params1 = param_stack.pop()
    _, best_params2 = param_stack.pop()
    _, best_params3 = param_stack.pop()

    print(best_params1)
    print(best_params2)
    print(best_params3)

    score_func1 = generate_score_function(*best_params1)
    score_func2 = generate_score_function(*best_params2)
    score_func3 = generate_score_function(*best_params3)

    test_agents    = [
        Agent(AlphaBetaPlayer(score_fn=improved_score), "AB_Improved"),
        Agent(AlphaBetaPlayer(score_fn=score_func1), "AB_Custom_1"),
        Agent(AlphaBetaPlayer(score_fn=score_func2), "AB_Custom_2"),
        Agent(AlphaBetaPlayer(score_fn=score_func3), "AB_Custom_3"),
    ]

    print("{:^74}".format("*************************"))
    print("{:^74}".format("Playing Matches"))
    print("{:^74}".format("*************************"))
    tournament_play_matches(cpu_agents, test_agents, NUM_MATCHES)

if __name__ == "__main__":
    optimize()
