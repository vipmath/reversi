from __future__ import division

from boardplayer import player
from random import random, choice
from math import log, sqrt
import datetime
import reversi


class MonteCarlo(player.Player):
    def __init__(self, board, **kwargs):
        super(MonteCarlo, self).__init__(board)
        self.max_moves = 60
        self.max_nodes = 200000
        self.max_time = datetime.timedelta(seconds=60)
        self.C = kwargs.get('C', 1.1)

        self.wins = {1: {}, 2: {}}
        self.plays = {1: {}, 2: {}}

    def get_play(self):
        state = self.states[-1]
        player = state[2]
        legal = self.board.legal_plays(state)
        _legal = self.board._legal_plays(state)
        assert set(legal) == set(_legal)

        if not legal:
            return
        if len(legal) == 1:
            return legal[0]

        begin, games = datetime.datetime.utcnow(), 0
        while datetime.datetime.utcnow() - begin < self.max_time:
            self.random_game()
            games += 1

        print games, datetime.datetime.utcnow() - begin
        states = [(self.board.play(state, p), p) for p in legal]
        move = max((self.wins[player][S] / self.plays[player][S],
                    self.plays[player][S], p)
                   for S, p in states)[2]

        for x in sorted(((100 * self.wins[player][S] / self.plays[player][S],
                          self.wins[player][S], self.plays[player][S], p)
                         for S, p in states), reverse=True):
            print "{3}: {0:.2f}% ({1} / {2})".format(*x)

        return move

    def random_game(self):
        game_moves = {1: set(), 2: set()}
        new_states = self.states[:]

        expand = True
        for t in xrange(self.max_moves):
            state = new_states[-1]
            p1_placed, p2_placed, player = state
            legal = self.board.legal_plays(state)
            states = [(self.board.play(state, p), p) for p in legal]
            if not states:
                print self.board.display(state)

            if all(self.plays[player].get(S) for S, p in states):
                plays, wins = self.plays[player], self.wins[player]
                log_total = log(sum(plays[S] for S, p in states) or 1)
                move = max(((wins[S] / plays[S]) +
                            self.C * sqrt(log_total / plays[S]), p)
                           for S, p in states)[1]
            else:
                move = choice(legal)

            state = self.board.play(state, move)
            new_states.append(state)

            if expand and state not in self.plays[player]:
                expand = False
                self.plays[player][state] = 0
                self.wins[player][state] = 0

            if state in self.plays[player]:
                game_moves[player].add(state)

            winner = self.board.winner(new_states)
            if winner:
                break

        for player, M in game_moves.iteritems():
            for S in M:
                self.plays[player][S] += 1
        if winner in (1, 2):
            for S in game_moves[winner]:
                self.wins[winner][S] += 1


if __name__ == '__main__':
    board = reversi.Board()
    player = MonteCarlo(board)
    player.run()
