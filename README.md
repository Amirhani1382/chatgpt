# Ping Pong Tournament Manager

This repository contains a simple command line program written in Python to
manage a table tennis (ping pong) tournament with group stage and knockout
stage.

## Usage

```
python pingpong_tournament.py [OPTIONS] player1 player2 ...
```

Players should be listed in seeding order. Use `--groups` to set the number of
groups and `--advance` for the number of players that advance from each group.
The program will prompt for match results during execution.

Example:

```
python pingpong_tournament.py --groups 2 --advance 2 Alice Bob Charlie Dave
```

The script then asks for results of each match and prints the champion.

## Open Trackin Website

To open [trackin.post.ir](https://trackin.post.ir) in Google Chrome, run:

```
python open_trackin_chrome.py
```

The script attempts to use Chrome if installed; otherwise it falls back to your default browser.

## Postal Tracking Web App Scaffold

Use `scaffold_post_tracking_app.py` to generate a starter project for a
modular Flask application that tracks Iranian postal codes. The script creates
directories for the backend, templates and static assets and fills them with
documented boilerplate code.

```
python scaffold_post_tracking_app.py /path/to/new/project
```

The target directory must be empty. After running the command you can navigate
into the generated folder, install dependencies and start implementing the
remaining features.
