#!/usr/bin/env python3

import os
import subprocess
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")

APPS = [
    ("YouTube", "https://www.youtube.com", "youtube.png"),
    ("SVT Play", "https://www.svtplay.se", "svtplay.png"),
    ("Netflix", "https://www.netflix.com", "netflix.png"),
]

BG_TOP = "#11141c"
BG_BOTTOM = "#050608"
TEXT = "#eeeeee"
SUBTEXT = "#777b84"

current = 0
tiles = []


def launch(url):
    subprocess.run([
        "chromium",
        "--kiosk",
        "--noerrdialogs",
        "--disable-infobars",
        "--disable-session-crashed-bubble",
        "--disable-features=Translate",
        url
    ])


def load_logo(filename, size):
    path = os.path.join(ASSETS, filename)

    image = Image.open(path).convert("RGBA")
    image.thumbnail(size, Image.Resampling.LANCZOS)

    return ImageTk.PhotoImage(image)


def select_tile(index):
    global current
    current = index

    for i, tile in enumerate(tiles):
        scale = 1.08 if i == current else 1.0
        tile["logo"].configure(
            image=tile["selected_logo"] if i == current
            else tile["normal_logo"]
        )

        tile["label"].configure(
            fg=TEXT if i == current else SUBTEXT
        )


def activate(event=None):
    launch(APPS[current][1])


def move_left(event=None):
    select_tile((current - 1) % len(APPS))


def move_right(event=None):
    select_tile((current + 1) % len(APPS))


# ------------------------------------------------------------
# Window
# ------------------------------------------------------------

root = tk.Tk()
root.title("Launcher")
root.attributes("-fullscreen", True)
root.configure(bg=BG_TOP)
root.config(cursor="none")


# ------------------------------------------------------------
# Ambient background
# ------------------------------------------------------------

width = root.winfo_screenwidth()
height = root.winfo_screenheight()

background = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(background)

top = (17, 20, 28)
bottom = (5, 6, 8)

for y in range(height):
    t = y / height

    color = tuple(
        int(top[i] * (1 - t) + bottom[i] * t)
        for i in range(3)
    )

    draw.line((0, y, width, y), fill=color)

# Add a very subtle blurred glow in the centre
glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow)

glow_draw.ellipse(
    (
        width * 0.25,
        height * 0.05,
        width * 0.75,
        height * 0.85,
    ),
    fill=(60, 70, 100, 35)
)

glow = glow.filter(ImageFilter.GaussianBlur(150))
background = Image.alpha_composite(
    background.convert("RGBA"),
    glow
)

background_photo = ImageTk.PhotoImage(background)

background_label = tk.Label(
    root,
    image=background_photo,
    bd=0
)
background_label.place(x=0, y=0, relwidth=1, relheight=1)


# ------------------------------------------------------------
# Title
# ------------------------------------------------------------

title = tk.Label(
    root,
    text="What do you want to watch?",
    font=("sans-serif", 26),
    fg=TEXT,
    bg=BG_TOP
)

title.place(
    relx=0.5,
    rely=0.20,
    anchor="center"
)


# ------------------------------------------------------------
# App tiles
# ------------------------------------------------------------

container = tk.Frame(root, bg=BG_TOP)
container.place(
    relx=0.5,
    rely=0.52,
    anchor="center"
)

for name, url, filename in APPS:

    normal_logo = load_logo(filename, (260, 130))
    selected_logo = load_logo(filename, (280, 140))

    frame = tk.Frame(
        container,
        width=300,
        height=190,
        bg=BG_TOP
    )
    frame.pack(side="left", padx=25)

    frame.pack_propagate(False)

    logo = tk.Label(
        frame,
        image=normal_logo,
        bg=BG_TOP,
        bd=0
    )
    logo.pack(pady=(15, 8))

    label = tk.Label(
        frame,
        text=name,
        font=("sans-serif", 16),
        fg=SUBTEXT,
        bg=BG_TOP
    )
    label.pack()

    tiles.append({
        "frame": frame,
        "logo": logo,
        "label": label,
        "normal_logo": normal_logo,
        "selected_logo": selected_logo,
    })


# ------------------------------------------------------------
# Keyboard controls
# ------------------------------------------------------------

root.bind("<Left>", move_left)
root.bind("<Right>", move_right)
root.bind("<Return>", activate)

# Escape is useful while developing.
root.bind("<Escape>", lambda e: root.destroy())


# Initial selection
select_tile(0)

root.mainloop()