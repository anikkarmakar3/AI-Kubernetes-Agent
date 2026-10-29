
from pathlib import Path
import shutil

from langchain.tools import tool

ROOT = Path(__file__).resolve().parent
BACKUPS = ROOT / ".agent_backups"

IGNORED = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".agent_backups",
    ".env",
}

PROTECTED = {
    ".env",
    ".env.local",
    ".gitignore",
    "requirements.txt",
}


def safe_path(relative_path: str) -> Path:
    path = (ROOT / relative_path).resolve()

    if not path.is_relative_to(ROOT):
        raise ValueError("Path must stay inside the project.")

    parts = path.relative_to(ROOT).parts

    if any(part in IGNORED for part in parts):
        raise ValueError("Access to this path is restricted.")

    if path.name in PROTECTED or path.name.startswith(".env"):
        raise ValueError("This file is protected.")

    # Protect Markdown files from accidental overwrites.
    if path.suffix.lower() == ".md":
        raise ValueError("Markdown files are read-only.")

    return path


@tool
def list_files() -> str:
    """List files in the project, excluding secrets and generated folders."""
    results = []

    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)

        if any(part in IGNORED for part in relative.parts):
            continue

        if path.is_file() and not path.name.startswith("."):
            results.append(str(relative))

    return "\n".join(sorted(results)[:300]) or "No files found."


@tool
def read_file(relative_path: str) -> str:
    """Read a UTF-8 text file inside the project directory."""
    path = (ROOT / relative_path).resolve()

    if not path.is_relative_to(ROOT):
        return "Error: path is outside the project."

    if any(part in IGNORED for part in path.relative_to(ROOT).parts):
        return "Error: access restricted."

    if path.name.startswith(".env"):
        return "Error: environment files are protected."

    if not path.is_file():
        return "Error: file not found."

    if path.stat().st_size > 200_000:
        return "Error: file is too large to read in one operation."

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "Error: this is not a UTF-8 text file."


@tool
def write_file(relative_path: str, content: str) -> str:
    """Create or update a file after asking the user for confirmation."""
    try:
        path = safe_path(relative_path)
    except ValueError as exc:
        return f"Error: {exc}"

    if path.is_dir():
        return "Error: cannot overwrite a directory."

    if len(content.encode("utf-8")) > 200_000:
        return "Error: file exceeds the 200 KB limit."

    if path.exists() and not path.is_file():
        return "Error: destination is not a regular file."

    print(f"\nProposed file change: {path.relative_to(ROOT)}")
    print(f"Operation: {'update' if path.exists() else 'create'}")

    if input("Approve this change? [y/N]: ").strip().lower() != "y":
        return "User declined the file change."

    if path.exists():
        backup = BACKUPS / path.relative_to(ROOT)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    return f"Successfully wrote {path.relative_to(ROOT)}"

