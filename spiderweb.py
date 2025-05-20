#!/usr/bin/env python3

import subprocess
import re
import sys
import os
import time
import argparse
import tempfile
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from collections import defaultdict

console = Console()

KOKO_QUOTES = [
    "Weapons are just tools. I prefer to sell concepts.",
    "I like war. It’s a business where I can be myself.",
    "In a world of monsters, I’ll be the devil they fear.",
    "Peace is just a lull in business.",
    "There’s no place for hesitation on the battlefield.",
    "Let’s get this party started. Shall we paint the world red?",
]

def flashy_banner():
    art = r"""
     ██████  ██████  ██ ██████  ███████ ██████  ██    ██ ███████ ██████  
    ██      ██    ██ ██ ██   ██ ██      ██   ██ ██    ██ ██      ██   ██ 
    ██      ██    ██ ██ ██████  █████   ██████  ██    ██ █████   ██   ██ 
    ██      ██    ██ ██ ██   ██ ██      ██   ██ ██    ██ ██      ██   ██ 
     ██████  ██████  ██ ██   ██ ███████ ██   ██  ██████  ███████ ██████  
    """
    quote = Text(f"\nKoko says: \"{KOKO_QUOTES[int(time.time()) % len(KOKO_QUOTES)]}\"", style="bold magenta")
    console.print(Text(art, style="bold red"))
    console.print(quote)
    console.rule()

def parse_line(line, data_store):
    patterns = {
        "IP Addresses": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        "Emails": r'[\w\.-]+@[\w\.-]+',
        "Domains": r'(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}',
        "Dark Web Mentions": r'[a-zA-Z0-9]{16}\.onion',
        "Encryption Keys": r'(?:ssh-rsa|ssh-ed25519) AAAA[0-9A-Za-z+/=]+',
        "Credentials": r'(user:.*?pass:.*?)\\n',
    }
    for category, pattern in patterns.items():
        matches = re.findall(pattern, line)
        for match in matches:
            data_store[category].add(match)

def create_tables(data_store):
    tables = []
    for section, items in data_store.items():
        if not items:
            continue
        table = Table(title=section, style="cyan")
        table.add_column("#", justify="right", style="bold green")
        table.add_column("Value", style="white")
        for i, item in enumerate(sorted(items)):
            table.add_row(str(i + 1), item)
        tables.append(Panel(table, title=f"[bold red]{section}"))
    if not tables:
        tables.append(Panel(Text("Waiting for results...", style="dim"), title="SpiderWeb"))
    return tables

def tail_file(filepath, data_store):
    with open(filepath, 'r') as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            parse_line(line, data_store)
            yield create_tables(data_store)

def find_spiderfoot():
    paths = ["./sfcli.py", "/usr/local/bin/sfcli.py", "/opt/spiderfoot/sfcli.py"]
    for path in paths:
        if os.path.isfile(path):
            return path
    return "sfcli.py"  # fallback if it's in PATH

def launch_spiderfoot(target, output_file):
    sf_path = find_spiderfoot()
    return subprocess.Popen([
        "python3", sf_path, "-s", "all", "-t", target
    ], stdout=open(output_file, "w", buffering=1), stderr=subprocess.STDOUT)

def open_new_terminal(script_path, logfile):
    terminal_cmds = [
        ["gnome-terminal", "--", "python3", script_path, "--watch", logfile],
        ["xfce4-terminal", "--command", f"python3 {script_path} --watch {logfile}"],
        ["xterm", "-e", f"python3 {script_path} --watch {logfile}"],
        ["kitty", "python3", script_path, "--watch", logfile],
        ["alacritty", "-e", "python3", script_path, "--watch", logfile],
    ]
    for cmd in terminal_cmds:
        try:
            subprocess.Popen(cmd)
            return
        except FileNotFoundError:
            continue
    console.print("[bold red]Error:[/] No supported terminal emulator found to launch live view.")

def main():
    parser = argparse.ArgumentParser(description="SpiderWeb - Full Integration with SpiderFoot")
    parser.add_argument("--target", metavar="TARGET", help="Target for SpiderFoot scan")
    parser.add_argument("--watch", metavar="LOGFILE", help="Internal use only: Watch log file")
    args = parser.parse_args()

    if args.watch:
        flashy_banner()
        data_store = defaultdict(set)
        with Live(console=console, screen=True, refresh_per_second=3) as live:
            for tables in tail_file(args.watch, data_store):
                layout = Layout()
                layout.split_column(*[Layout(t) for t in tables])
                live.update(layout)
    elif args.target:
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmpfile:
            logfile = tmpfile.name
        script_path = os.path.realpath(__file__)
        proc = launch_spiderfoot(args.target, logfile)
        time.sleep(2)
        open_new_terminal(script_path, logfile)
    else:
        console.print("[bold red]Usage:[/] spiderweb.py --target <domain/ip>")

if __name__ == "__main__":
    main()
