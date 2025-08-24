import os
import re
import subprocess
from typing import Tuple


def _run(cmd: list, cwd: str | None = None) -> Tuple[int, str, str]:
    """Run a shell command and return (code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError as e:
        # Likely git is not installed
        return 127, "", str(e)


def parse_repo_url(settings_path: str) -> str | None:
    """Extract the first GitHub .git URL from the settings markdown file."""
    if not os.path.exists(settings_path):
        return None
    with open(settings_path, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.search(r"https://github.com/[\w\-./]+\.git", content)
    return m.group(0) if m else None


def _effective_base_dir(base_dir: str) -> str:
    """Return a writable base dir. If base_dir is not writable (e.g., /opt),
    fall back to ~/.local/share/shota.
    """
    try:
        if os.path.isdir(base_dir) and os.access(base_dir, os.W_OK):
            return base_dir
    except Exception:
        pass
    home = os.path.expanduser("~")
    fallback = os.path.join(home, ".local", "share", "shota")
    os.makedirs(fallback, exist_ok=True)
    return fallback


def get_repo_path(base_dir: str, settings_path: str) -> Tuple[str | None, str]:
    """Compute the intended local repository path (with writable fallback).

    Returns (url, repo_path). If URL cannot be parsed, (None, base_dir_or_fallback).
    """
    url = parse_repo_url(settings_path)
    eff_base = _effective_base_dir(base_dir)
    if not url:
        return None, eff_base
    repo_name = os.path.splitext(os.path.basename(url))[0]
    return url, os.path.join(eff_base, repo_name)


def ensure_repo(base_dir: str, settings_path: str) -> Tuple[bool, str, str]:
    """
    Ensure the local repo (derived from settings) exists and is up to date.

    Returns: (changed, repo_path, message)
      - changed: True if cloned or updated, False otherwise
      - repo_path: local path where the repo lives (or intended to live)
      - message: human-readable status
    """
    url, repo_path = get_repo_path(base_dir, settings_path)
    if not url:
        return False, repo_path, "რეპოზიტორის URL ვერ მოიძებნა githubSettings.md-ში"

    # Verify git availability
    code, out, err = _run(["git", "--version"])    
    if code != 0:
        return False, repo_path, f"Git არ არის დაყენებული ან PATH-ში (შეცდომა: {err or out})"

    if not os.path.exists(repo_path) or not os.path.isdir(os.path.join(repo_path, ".git")):
        # Clone fresh
        os.makedirs(os.path.dirname(repo_path), exist_ok=True)
        code, out, err = _run(["git", "clone", url, repo_path])
        if code != 0:
            return False, repo_path, f"კლონირება ვერ მოხერხდა: {err or out}"
        return True, repo_path, "რეპოზიტორი დაკლონდა"

    # Existing repo: fetch and see if we are behind upstream
    code, out, err = _run(["git", "fetch", "--prune"], cwd=repo_path)
    if code != 0:
        return False, repo_path, f"fetch შეცდომა: {err or out}"

    # Determine current branch
    code, branch, err = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path)
    if code != 0 or not branch:
        branch = "main"

    # Determine upstream, fallback to origin/main
    code, upstream, err = _run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=repo_path)
    if code != 0 or not upstream:
        upstream = f"origin/{branch}"

    # How many commits behind?
    code, behind, err = _run(["git", "rev-list", "--count", f"HEAD..{upstream}"], cwd=repo_path)
    if code != 0:
        # As a fallback, compare remote HEAD of branch
        code2, ls, err2 = _run(["git", "ls-remote", "--heads", "origin", branch], cwd=repo_path)
        if code2 == 0 and ls:
            remote_sha = ls.split()[0]
            code3, local_sha, err3 = _run(["git", "rev-parse", "HEAD"], cwd=repo_path)
            if code3 == 0 and local_sha and local_sha != remote_sha:
                # Pull
                pcode, pout, perr = _run(["git", "pull", "--rebase"], cwd=repo_path)
                if pcode == 0:
                    return True, repo_path, "რეპოზიტორი განახლდა"
                return False, repo_path, f"pull შეცდომა: {perr or pout}"
            return False, repo_path, "უკვე უახლესია"
        return False, repo_path, f"ვერსიის შედარება ვერ მოხერხდა: {err or behind}"

    try:
        behind_n = int(behind.strip())
    except ValueError:
        behind_n = 0

    if behind_n > 0:
        code, out, err = _run(["git", "pull", "--rebase"], cwd=repo_path)
        if code != 0:
            return False, repo_path, f"განახლება ვერ მოხერხდა: {err or out}"
        return True, repo_path, "რეპოზიტორი განახლდა"

    return False, repo_path, "უკვე უახლესია"
