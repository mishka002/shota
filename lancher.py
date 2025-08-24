import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import sys
import os
import argparse
from updater import ensure_repo, get_repo_path

# Try to use ttkbootstrap for modern theming if available
try:
    import ttkbootstrap as tb
    THEMED = True
except Exception:
    tb = None
    THEMED = False


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_PATH = os.path.join(BASE_DIR, "githubSettings.md")


def run_update_async(status_var: tk.StringVar, button: tk.Button, pbar: ttk.Progressbar | None = None, on_done=None):
    def task():
        try:
            button.config(state=tk.DISABLED)
            status_var.set("მიმდინარეობს შემოწმება…")
            changed, repo_path, msg = ensure_repo(BASE_DIR, SETTINGS_PATH)
            if changed:
                status_var.set(f"OK: {msg}")
            else:
                status_var.set(msg)
        except Exception as e:
            status_var.set(f"შეცდომა: {e}")
        finally:
            button.config(state=tk.NORMAL)
            try:
                if pbar is not None:
                    pbar.stop()
            except Exception:
                pass
            if callable(on_done):
                try:
                    on_done()
                except Exception:
                    pass

    threading.Thread(target=task, daemon=True).start()


def main():
    parser = argparse.ArgumentParser(description="Shota გამშვები")
    parser.add_argument("--autorun", action="store_true", help="განახლების შემდეგ ავტომატურად გაუშვი კალკულატორი")
    args = parser.parse_args()
    # Create window with theme if possible
    if THEMED:
        root = tb.Window(themename="flatly")
    else:
        root = tk.Tk()
    root.title("გამშვები")

    # Container frame
    container = ttk.Frame(root, padding=(16, 12))
    container.pack(fill="both", expand=True)

    # Header
    title_style = {"font": ("Segoe UI", 14, "bold")}
    if THEMED:
        header = ttk.Label(container, text="🚀 ალფა გამშვები", **title_style)
    else:
        header = ttk.Label(container, text="ალფა გამშვები", **title_style)
    header.pack(anchor="w", pady=(0, 10))

    # Status line
    status_var = tk.StringVar(value="მზადაა")
    status_row = ttk.Frame(container)
    status_row.pack(fill="x", pady=(0, 8))
    ttk.Label(status_row, text="სტატუსი:").pack(side="left")
    status_label = ttk.Label(status_row, textvariable=status_var)
    status_label.pack(side="left", padx=(6, 0))

    # Progress bar
    pbar = ttk.Progressbar(container, mode="indeterminate")
    pbar.pack(fill="x", pady=(0, 12))

    # Buttons row
    btns = ttk.Frame(container)
    btns.pack(fill="x")

    # Styled button if ttkbootstrap present
    if THEMED:
        update_btn = tb.Button(btns, text="გითჰაბის შემოწმება/განახლება", bootstyle="primary")
        run_btn = tb.Button(btns, text="კალკულატორის გაშვება", bootstyle="success")
        quit_btn = tb.Button(btns, text="გასვლა", bootstyle="secondary", command=root.destroy)
    else:
        update_btn = ttk.Button(btns, text="გითჰაბის შემოწმება/განახლება")
        run_btn = ttk.Button(btns, text="კალკულატორის გაშვება")
        quit_btn = ttk.Button(btns, text="გასვლა", command=root.destroy)

    def run_calculator():
        exe = sys.executable or "python3"
        # Prefer running the updated home.py from the cloned repo if available
        url, repo_path = get_repo_path(BASE_DIR, SETTINGS_PATH)
        candidate = os.path.join(repo_path, "home.py") if repo_path else None
        home_py = candidate if candidate and os.path.isfile(candidate) else os.path.join(BASE_DIR, "home.py")
        try:
            subprocess.Popen([exe, home_py])
            status_var.set("კალკულატორი გაეშვა")
        except Exception as e:
            status_var.set(f"ვერ გაიშვა: {e}")

    def start_update():
        # Wire indeterminate progress
        try:
            pbar.start(70)
        except Exception:
            pass
        run_update_async(status_var, update_btn, pbar, on_done=(run_calculator if args.autorun else None))

    update_btn.config(command=start_update)
    run_btn.config(command=run_calculator)

    update_btn.pack(side="left")
    run_btn.pack(side="left", padx=(8, 0))
    btns.pack_propagate(False)
    quit_btn.pack(side="right")

    # Auto-check shortly after start
    root.after(250, start_update)

    root.mainloop()


if __name__ == "__main__":
    main()