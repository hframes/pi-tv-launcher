#!/usr/bin/env python3

import subprocess
import tkinter as tk

APPS = {
    "YouTube": "https://www.youtube.com",
    "SVT Play": "https://www.svtplay.se",
    "Netflix": "https://www.netflix.com",
}

def launch(url):
    subprocess.run([
        "chromium",
        "--kiosk",
        "--noerrdialogs",
        "--disable-infobars",
        url
    ])

root = tk.Tk()
root.title("Launcher")
root.attributes("-fullscreen", True)

for name, url in APPS.items():
    tk.Button(
        root,
        text=name,
        font=("sans-serif", 28),
        command=lambda u=url: launch(u)
    ).pack(fill="both", expand=True, padx=40, pady=15)

root.bind("<Escape>", lambda e: root.destroy())

root.mainloop()
