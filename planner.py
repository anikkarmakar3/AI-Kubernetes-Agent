
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def find_markdown_files():
    ignored = {
        ".git",
        ".venv",
        "node_modules",
        ".agent_backups",
    }

    return [
        path for path in ROOT.rglob("*.md")
        if not any(part in ignored for part in path.relative_to(ROOT).parts)
    ]


def load_specification():
    files = find_markdown_files()

    if not files:
        raise FileNotFoundError(
            "No Markdown specification found in the project."
        )

    print("\nAvailable Markdown files:")

    for index, path in enumerate(files, start=1):
        print(f"{index}. {path.relative_to(ROOT)}")

    choice = input("Select your main specification number: ").strip()

    if not choice.isdigit():
        raise ValueError("Please enter a valid number.")

    index = int(choice) - 1

    if index < 0 or index >= len(files):
        raise ValueError("Selection is out of range.")

    selected = files[index]
    content = selected.read_text(encoding="utf-8")

    if len(content) > 100_000:
        raise ValueError(
            "Specification is too large. Split it into smaller files."
        )

    return selected, content


def build_review_prompt(spec_path, specification):
    return f"""
Review this existing project using the specification below.

Specification file: {spec_path.name}

SPECIFICATION:
{specification}

Tasks:
1. Summarize the required features.
2. Inspect existing project files using the available tools.
3. Identify completed, incomplete, and missing features.
4. Recommend the next three implementation tasks.
5. Do not change any files during this review.
6. Do not claim that tests passed unless they were actually run.

Return a concise implementation status report.
"""

