# Ping Pong Tournament Manager

This repository contains a simple command line program written in Python to
manage a table tennis (ping pong) tournament with group stage and knockout
stage.

## Usage

```
python pingpong_tournament.py [OPTIONS] player1 player2 ...
```

Players must be listed in seeding order. Use `--groups` to set the number of
groups and `--advance` for the number of players that advance from each group.
The program will prompt for match results during execution.

Example:

```
python pingpong_tournament.py --groups 2 --advance 2 Alice Bob Charlie Dave
```

The script then asks for results of each match and prints the champion.
