# Ping Pong Tournament Manager

This repository contains a simple program written in Python to manage a table
tennis (ping pong) tournament with group and knockout stages. Two interfaces
are provided: a command line tool and a graphical user interface built with
Tkinter.

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


### Graphical Interface

Run the GUI with:

```
python pingpong_gui.py
```

Enter the player names in seeding order and configure the number of groups.
Results can be entered by double-clicking matches in the group or knockout
views. The champion is displayed once all rounds are complete.
