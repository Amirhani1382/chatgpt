# pingpong_tournament.py
"""Ping Pong Tournament Management.

This module provides classes to manage a table tennis tournament
with group (round robin) and knockout stages.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
import math
import itertools

@dataclass
class Player:
    name: str
    seed: int = 0
    group: Optional[str] = None
    id: Optional[int] = None

    def __hash__(self):
        """Allow players to be dictionary keys using their name and seed."""
        return hash((self.name, self.seed))


@dataclass
class MatchResult:
    player1: Player
    player2: Player
    scores: List[Tuple[int, int]]  # list of tuples (p1_score, p2_score)

    @property
    def winner(self) -> Player:
        p1_sets = sum(1 for a, b in self.scores if a > b)
        p2_sets = sum(1 for a, b in self.scores if b > a)
        return self.player1 if p1_sets > p2_sets else self.player2


def snake_seed(players: List[Player], group_count: int) -> Dict[str, List[Player]]:
    """Distribute players into groups using snake seeding."""
    groups = {f"G{i+1}": [] for i in range(group_count)}
    direction = 1
    group_index = 0
    for p in sorted(players, key=lambda x: x.seed):
        key = f"G{group_index+1}"
        groups[key].append(p)
        group_index += direction
        if group_index == group_count:
            direction = -1
            group_index = group_count - 1
        elif group_index < 0:
            direction = 1
            group_index = 0
    return groups

@dataclass
class Group:
    name: str
    players: List[Player]
    matches: List[MatchResult] = field(default_factory=list)
    schedule: List[Tuple[Player, Player]] = field(default_factory=list)

    def schedule_matches(self) -> List[Tuple[Player, Player]]:
        """Generate and store all match pairings for this group."""
        self.schedule = list(itertools.combinations(self.players, 2))
        return self.schedule

    def record_result(self, p1: Player, p2: Player, scores: List[Tuple[int, int]]):
        self.matches.append(MatchResult(p1, p2, scores))

    def standings(self) -> List[Tuple[Player, int, int]]:
        points: Dict[Player, int] = {p: 0 for p in self.players}
        for match in self.matches:
            winner = match.winner
            loser = match.player1 if winner is match.player2 else match.player2
            points[winner] += 2
            points[loser] += 1
        standings = sorted(points.items(), key=lambda x: (-x[1], x[0].seed))
        return [(p, pts, i) for i, (p, pts) in enumerate(standings, 1)]

    def is_complete(self) -> bool:
        """Return True if all scheduled matches have results."""
        return len(self.matches) == len(self.schedule)

@dataclass
class KnockoutMatch:
    player1: Optional[Player]
    player2: Optional[Player]
    result: Optional[MatchResult] = None

    @property
    def is_ready(self) -> bool:
        return self.player1 is not None and self.player2 is not None

@dataclass
class KnockoutBracket:
    rounds: List[List[KnockoutMatch]] = field(default_factory=list)

    @classmethod
    def from_players(cls, players: List[Player]):
        size = 1
        while size < len(players):
            size *= 2
        bracket_players = players + [None] * (size - len(players))

        first_round = [
            KnockoutMatch(bracket_players[i], bracket_players[i + 1])
            for i in range(0, size, 2)
        ]
        rounds = [first_round]
        matches = first_round
        while len(matches) > 1:
            matches = [KnockoutMatch(None, None) for _ in range(len(matches) // 2)]
            rounds.append(matches)
        return cls(rounds)

    def record_result(self, round_index: int, match_index: int, scores: List[Tuple[int, int]]):
        match = self.rounds[round_index][match_index]
        match.result = MatchResult(match.player1, match.player2, scores)
        winner = match.result.winner
        if round_index + 1 < len(self.rounds):
            next_match = self.rounds[round_index+1][match_index//2]
            if match_index % 2 == 0:
                next_match.player1 = winner
            else:
                next_match.player2 = winner

    def champion(self) -> Optional[Player]:
        final = self.rounds[-1][0]
        if final.result:
            return final.result.winner
        if final.player1 and not final.player2:
            return final.player1
        if final.player2 and not final.player1:
            return final.player2
        return None

class Tournament:
    def __init__(self, players: List[Player], group_count: int = 4, advance_per_group: int = 2):
        self.players = players
        self.group_count = group_count
        self.advance_per_group = advance_per_group
        self.groups: Dict[str, Group] = {}
        self.bracket: Optional[KnockoutBracket] = None

    def create_groups(self):
        assignments = snake_seed(self.players, self.group_count)
        for name, players in assignments.items():
            self.groups[name] = Group(name, players)
        return self.groups

    def group_standings(self, name: str):
        return self.groups[name].standings()

    def advance_players(self) -> List[Player]:
        qualified = []
        for g in self.groups.values():
            standings = g.standings()
            qualified.extend([p for p, _, pos in standings[:self.advance_per_group]])
        return qualified

    def create_bracket(self, players: List[Player]):
        self.bracket = KnockoutBracket.from_players(players)
        return self.bracket


# Sample usage via command line
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ping Pong Tournament Manager")
    parser.add_argument('players', nargs='*', help='List of player names in seeding order')
    parser.add_argument('--groups', type=int, default=4, help='Number of groups')
    parser.add_argument('--advance', type=int, default=2, help='Number advancing from each group')
    args = parser.parse_args()
    if not args.players:
        parser.print_usage()
        print("error: the following arguments are required: players")
        raise SystemExit(1)

    players = [Player(name, seed=i+1) for i, name in enumerate(args.players)]
    t = Tournament(players, group_count=args.groups, advance_per_group=args.advance)

    t.create_groups()
    for g in t.groups.values():
        print(f"\nGroup {g.name}")
        for p in g.players:
            print(f"  {p.seed}. {p.name}")
        schedule = g.schedule_matches()
        for p1, p2 in schedule:
            print(f"Enter result for {p1.name} vs {p2.name} (comma separated sets e.g. 11-7,7-11,11-9):")
            line = input().strip()
            sets = [(int(a), int(b)) for a,b in (s.split('-') for s in line.split(','))]
            g.record_result(p1, p2, sets)
        standings = g.standings()
        print("Standings:")
        for player, pts, pos in standings:
            print(f"{pos}. {player.name} - {pts} pts")

    advancing = t.advance_players()
    print("\nAdvancing to knockout:")
    for p in advancing:
        print(p.name)
    bracket = t.create_bracket(advancing)
    # display round names
    size = len(bracket.rounds[0]) * 2
    round_names = []
    for _ in bracket.rounds:
        round_names.append(f"Round of {size}")
        size //= 2
    for rnd, name in enumerate(round_names):
        print(f"\n{name}")
        for idx, match in enumerate(bracket.rounds[rnd]):
            if match.player1 and match.player2:
                print(f"Enter result for {match.player1.name} vs {match.player2.name} sets:")
                line = input().strip()
                sets = [(int(a), int(b)) for a,b in (s.split('-') for s in line.split(','))]
                bracket.record_result(rnd, idx, sets)
            elif match.player1 or match.player2:
                winner = match.player1 or match.player2
                print(f"{winner.name} receives a bye")
                if rnd + 1 < len(bracket.rounds):
                    next_match = bracket.rounds[rnd+1][idx//2]
                    if idx % 2 == 0:
                        next_match.player1 = winner
                    else:
                        next_match.player2 = winner
    final_round = bracket.rounds[-1][0]
    champion = final_round.result.winner if final_round.result else (final_round.player1 or final_round.player2)
    print(f"\nChampion: {champion.name}")
