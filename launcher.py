#!/usr/bin/env python3

import os
import subprocess
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFilter


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")

APPS = [
    ("YouTube", "https://www.youtube.com", "youtube.png"),
    ("SVT Play", "https://www.svtplay.se", "svtplay.png"),
    ("Netflix", "https://www.netflix.com", "netflix.png"),
]

BG_TOP = "#11141c"
BG_BOTTOM = "#050608"

CARD = "#20242d"
CARD_SELECTED = "#303643"

TEXT = "#eeeeee"
SUBTEXT = "#888d97"


# ------------------------------------------------------------
# Launch applications
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Rounded rectangle helper
# ------------------------------------------------------------

def rounded_rectangle(canvas, x1, y1, x2, y2, radius, fill):
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2 - radius,
        x1, y1 + radius,
    ]

    return canvas.create_polygon(
        points,
        fill=fill,
        smooth=True
    )


# ------------------------------------------------------------
# Load and resize logo
# ------------------------------------------------------------

def load_logo(filename, max_size):
    path = os.path.join(ASSETS, filename)

    image = Image.open(path).convert("RGBA")
    image.thumbnail(max_size, Image.Resampling.LANCZOS)

    return ImageTk.PhotoImage(image)


# ------------------------------------------------------------
# Window
# ------------------------------------------------------------

root = tk.Tk()
root.title("Launcher")
root.attributes("-fullscreen", True)
root.configure(bg=BG_TOP)
root.config(cursor="")

width = root.winfo_screenwidth()
height = root.winfo_screenheight()


# ------------------------------------------------------------
# Ambient background
# ------------------------------------------------------------

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

    draw.line(
        (0, y, width, y),
        fill=color
    )


# Subtle central glow
glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
glow_draw = ImageDraw.Draw(glow)

glow_draw.ellipse(
    (
        width * 0.20,
        height * 0.05,
        width * 0.80,
        height * 0.90,
    ),
    fill=(65, 75, 105, 32)
)

glow = glow.filter(
    ImageFilter.GaussianBlur(160)
)

background = Image.alpha_composite(
    background.convert("RGBA"),
    glow
)

background_photo = ImageTk.PhotoImage(background)


# ------------------------------------------------------------
# Canvas
# ------------------------------------------------------------

canvas = tk.Canvas(
    root,
    width=width,
    height=height,
    highlightthickness=0,
    bd=0
)

canvas.pack(fill="both", expand=True)

canvas.create_image(
    0,
    0,
    image=background_photo,
    anchor="nw"
)


# ------------------------------------------------------------
# Title
# ------------------------------------------------------------

canvas.create_text(
    width / 2,
    height * 0.20,
    text="What do you want to watch?",
    font=("sans-serif", 26),
    fill=TEXT
)


# ------------------------------------------------------------
# Tiles
# ------------------------------------------------------------

tiles = []
current = 0

card_width = 300
card_height = 190
gap = 35

total_width = (
    len(APPS) * card_width
    + (len(APPS) - 1) * gap
)

start_x = (width - total_width) / 2
center_y = height * 0.53


for index, (name, url, filename) in enumerate(APPS):

    x1 = start_x + index * (card_width + gap)
    y1 = center_y - card_height / 2
    x2 = x1 + card_width
    y2 = y1 + card_height

    card = rounded_rectangle(
        canvas,
        x1,
        y1,
        x2,
        y2,
        28,
        CARD
    )

    logo = load_logo(
        filename,
        (240, 110)
    )

    logo_item = canvas.create_image(
        (x1 + x2) / 2,
        y1 + 82,
        image=logo,
        anchor="center"
    )

    label = canvas.create_text(
        (x1 + x2) / 2,
        y2 - 32,
        text=name,
        font=("sans-serif", 16),
        fill=SUBTEXT
    )

    tiles.append({
        "card": card,
        "logo": logo_item,
        "label": label,
        "normal_fill": CARD,
        "selected_fill": CARD_SELECTED,
        "url": url,
        "logo_image": logo,
    })


# ------------------------------------------------------------
# Selection
# ------------------------------------------------------------

def select_tile(index):
    global current

    current = index

    for i, tile in enumerate(tiles):

        if i == current:
            canvas.itemconfigure(
                tile["card"],
                fill=tile["selected_fill"]
            )

            canvas.itemconfigure(
                tile["label"],
                fill=TEXT
            )

        else:
            canvas.itemconfigure(
                tile["card"],
                fill=tile["normal_fill"]
            )

            canvas.itemconfigure(
                tile["label"],
                fill=SUBTEXT
            )


# ------------------------------------------------------------
# Keyboard controls
# ------------------------------------------------------------

def move_left(event=None):
    select_tile(
        (current - 1) % len(tiles)
    )


def move_right(event=None):
    select_tile(
        (current + 1) % len(tiles)
    )


def activate(event=None):
    launch(
        tiles[current]["url"]
    )


root.bind("<Left>", move_left)
root.bind("<Right>", move_right)
root.bind("<Return>", activate)

# Development exit
root.bind(
    "<Escape>",
    lambda event: root.destroy()
)


# ------------------------------------------------------------
# Start
# ------------------------------------------------------------

select_tile(0)

root.mainloop()
