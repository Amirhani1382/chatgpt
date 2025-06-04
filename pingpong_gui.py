# pingpong_gui.py
"""Simple graphical interface for Ping Pong Tournament Manager."""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from typing import List

from pingpong_tournament import Player, Tournament


class StartFrame(ttk.Frame):
    def __init__(self, master, start_callback):
        super().__init__(master)
        self.start_callback = start_callback
        self.pack(fill="both", expand=True)

        ttk.Label(self, text="Players (one per line, in seed order):").pack(anchor="w")
        self.player_text = tk.Text(self, width=40, height=15)
        self.player_text.pack(fill="x", padx=5, pady=5)

        options = ttk.Frame(self)
        options.pack(fill="x", pady=5)
        ttk.Label(options, text="Number of groups:").grid(row=0, column=0, sticky="w")
        self.group_var = tk.IntVar(value=2)
        ttk.Entry(options, textvariable=self.group_var, width=5).grid(row=0, column=1)
        ttk.Label(options, text="Advance per group:").grid(row=0, column=2, padx=(10,0))
        self.advance_var = tk.IntVar(value=2)
        ttk.Entry(options, textvariable=self.advance_var, width=5).grid(row=0, column=3)

        ttk.Button(self, text="Create Tournament", command=self.on_start).pack(pady=10)

    def on_start(self):
        players = [name.strip() for name in self.player_text.get("1.0", "end").splitlines() if name.strip()]
        if len(players) < 2:
            messagebox.showerror("Error", "Enter at least two players")
            return
        player_objs = [Player(name, seed=i+1) for i, name in enumerate(players)]
        groups = self.group_var.get()
        advance = self.advance_var.get()
        self.start_callback(player_objs, groups, advance)


class GroupFrame(ttk.Frame):
    def __init__(self, master, tournament: Tournament, done_callback):
        super().__init__(master)
        self.tournament = tournament
        self.done_callback = done_callback
        self.pack(fill="both", expand=True)
        ttk.Label(self, text="Group Stage", font=("Arial", 14, "bold")).pack(pady=5)

        self.group_notebooks = ttk.Notebook(self)
        self.group_notebooks.pack(fill="both", expand=True)
        for name, group in self.tournament.groups.items():
            frame = ttk.Frame(self.group_notebooks)
            self.group_notebooks.add(frame, text=name)
            self.populate_group_frame(frame, group)

        ttk.Button(self, text="Proceed to Knockout", command=self.try_finish).pack(pady=5)

    def populate_group_frame(self, frame, group):
        schedule = group.schedule if group.schedule else group.schedule_matches()
        table = ttk.Treeview(frame, columns=("p1", "p2", "result"), show="headings")
        table.heading("p1", text="Player 1")
        table.heading("p2", text="Player 2")
        table.heading("result", text="Result")
        table.pack(fill="both", expand=True, padx=5, pady=5)
        for p1, p2 in schedule:
            table.insert("", "end", values=(p1.name, p2.name, ""))
        table.bind("<Double-1>", lambda e, g=group, t=table: self.enter_result(g, t))
        standings = ttk.Label(frame, text="")
        standings.pack(pady=5)
        frame.table = table
        frame.standings_label = standings
        self.update_standings(frame, group)

    def enter_result(self, group, table):
        item = table.focus()
        if not item:
            return
        values = table.item(item, "values")
        if values[2]:
            messagebox.showinfo("Info", "Result already entered")
            return
        p1_name, p2_name, _ = values
        res = simpledialog.askstring("Result", f"Enter sets for {p1_name} vs {p2_name} (e.g. 11-7,7-11,11-9)")
        if not res:
            return
        try:
            sets = [(int(a), int(b)) for a,b in (s.split('-') for s in res.split(','))]
        except Exception:
            messagebox.showerror("Error", "Invalid format")
            return
        p1 = next(p for p in group.players if p.name == p1_name)
        p2 = next(p for p in group.players if p.name == p2_name)
        group.record_result(p1, p2, sets)
        table.set(item, column="result", value=" ".join(f"{a}-{b}" for a,b in sets))
        self.update_standings(table.master, group)

    def update_standings(self, frame, group):
        standings = group.standings()
        text = "\n".join(f"{pos}. {p.name} ({pts} pts)" for p, pts, pos in standings)
        frame.standings_label.config(text=text)

    def try_finish(self):
        if not all(g.is_complete() for g in self.tournament.groups.values()):
            messagebox.showerror("Error", "Complete all group matches first")
            return
        self.done_callback()


class KnockoutFrame(ttk.Frame):
    def __init__(self, master, tournament: Tournament):
        super().__init__(master)
        self.tournament = tournament
        self.pack(fill="both", expand=True)
        ttk.Label(self, text="Knockout Stage", font=("Arial", 14, "bold")).pack(pady=5)

        self.bracket = self.tournament.create_bracket(self.tournament.advance_players())
        self.round_frames: List[ttk.Frame] = []
        for r_index, round_matches in enumerate(self.bracket.rounds):
            frame = ttk.LabelFrame(self, text=f"Round {r_index+1}")
            frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            self.round_frames.append(frame)
            for m_index, match in enumerate(round_matches):
                btn = ttk.Button(frame, text=self.match_text(match), command=lambda ri=r_index, mi=m_index: self.enter_result(ri, mi))
                btn.pack(fill="x", pady=2)
                match.button = btn
        self.status = ttk.Label(self, text="")
        self.status.pack(pady=5)
        self.update_status()

    def match_text(self, match):
        if match.player1 and match.player2:
            res = f"{match.player1.name} vs {match.player2.name}"
        elif match.player1 or match.player2:
            res = (match.player1 or match.player2).name + " (bye)"
        else:
            res = "TBD"
        if match.result:
            res += f" | winner: {match.result.winner.name}"
        return res

    def enter_result(self, r_index, m_index):
        match = self.bracket.rounds[r_index][m_index]
        if not match.is_ready:
            messagebox.showinfo("Info", "Match not ready yet")
            return
        if match.result:
            messagebox.showinfo("Info", "Result already entered")
            return
        res = simpledialog.askstring("Result", f"Enter sets for {match.player1.name} vs {match.player2.name}")
        if not res:
            return
        try:
            sets = [(int(a), int(b)) for a,b in (s.split('-') for s in res.split(','))]
        except Exception:
            messagebox.showerror("Error", "Invalid format")
            return
        self.bracket.record_result(r_index, m_index, sets)
        for rf in self.round_frames:
            for widget in rf.winfo_children():
                if isinstance(widget, ttk.Button):
                    match_btn = widget
                    text = self.match_text(getattr(match_btn, 'match', None))
        # refresh texts
        for ri, round_matches in enumerate(self.bracket.rounds):
            frame = self.round_frames[ri]
            for idx, widget in enumerate(frame.winfo_children()):
                match = round_matches[idx]
                widget.config(text=self.match_text(match))
        self.update_status()

    def update_status(self):
        champ = self.bracket.champion()
        if champ:
            self.status.config(text=f"Champion: {champ.name}")
        else:
            self.status.config(text="")


class TournamentApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ping Pong Tournament Manager")
        self.geometry("600x500")
        self.show_start()

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    def show_start(self):
        self.clear()
        StartFrame(self, self.start_tournament)

    def start_tournament(self, players: List[Player], groups: int, advance: int):
        self.tournament = Tournament(players, group_count=groups, advance_per_group=advance)
        self.tournament.create_groups()
        self.show_group_stage()

    def show_group_stage(self):
        self.clear()
        GroupFrame(self, self.tournament, self.show_knockout_stage)

    def show_knockout_stage(self):
        self.clear()
        KnockoutFrame(self, self.tournament)


if __name__ == "__main__":
    app = TournamentApp()
    app.mainloop()
