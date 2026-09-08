#!/usr/bin/env python3

import subprocess
import tkinter as tk

APPS = [
    ("YouTube", "https://www.youtube.com"),
    ("SVT Play", "https://www.svtplay.se"),
    ("Netflix", "https://www.netflix.com"),
]

BG = "#101114"
TILE = "#1c1e22"
TILE_ACTIVE = "#30333a"
TEXT = "#f2f2f2"
SUBTEXT = "#888b91"


def launch(url):
    subprocess.run([
        "chromium",
        "--kiosk",
        "--noerrdialogs",
        "--disable-infobars",
        "--disable-session-crashed-bubble",
        url
    ])


def focus_tile(index):
    for i, widget in enumerate(tiles):
        widget.configure(
            bg=TILE_ACTIVE if i == index else TILE
        )
    current = index


def activate(event=None):
    launch(APPS[current][1])


def move_left(event=None):
    global current
    current = (current - 1) % len(tiles)
    focus_tile(current)


def move_right(event=None):
    global current
    current = (current + 1) % len(tiles)
    focus_tile(current)


root = tk.Tk()
root.configure(bg=BG)
root.attributes("-fullscreen", True)
root.title("Launcher")

current = 0
tiles = []

# Title
title = tk.Label(
    root,
    text="What do you want to watch?",
    font=("sans-serif", 28),
    fg=TEXT,
    bg=BG
)
title.pack(pady=(100, 50))

# Tile container
container = tk.Frame(root, bg=BG)
container.pack(expand=True)

for name, url in APPS:
    tile = tk.Button(
        container,
        text=name,
        font=("sans-serif", 24),
        fg=TEXT,
        bg=TILE,
        activeforeground=TEXT,
        activebackground=TILE_ACTIVE,
        relief="flat",
        bd=0,
        width=14,
        height=5,
        highlightthickness=0,
        command=lambda u=url: launch(u)
    )
    tile.pack(side="left", padx=20)
    tiles.append(tile)

# Keyboard navigation
root.bind("<Left>", move_left)
root.bind("<Right>", move_right)
root.bind("<Return>", activate)
root.bind("<Escape>", lambda e: root.destroy())

focus_tile(0)

root.mainloop()
