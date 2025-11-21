"""Shared utility functions."""

import sys
from pathlib import Path
from typing import Optional


def print_formatted(text: str, max_line_length: int = 115) -> None:
    """
    Print text with word wrapping.

    Args:
        text: Text to print
        max_line_length: Maximum characters per line before wrapping
    """
    char_count = 0
    for char in text:
        if not (char == " " and char_count == 0):
            print(char, end="")
            char_count += 1
        if char_count > max_line_length and char == " ":
            print()
            char_count = 0
    print()
    sys.stdout.flush()


def write_to_file(filepath: Path, text: str, mode: str = 'a') -> None:
    """
    Write text to a file.

    Args:
        filepath: Path to the file
        text: Text to write
        mode: File mode ('a' for append, 'w' for write)

    Raises:
        IOError: If file write fails
    """
    try:
        with open(filepath, mode, encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        raise IOError(f"Failed to write to {filepath}: {e}")


def extract_essay(filepath: Path, essay_number: int) -> Optional[str]:
    """
    Extract a specific essay from a file with numbered essays.

    Expected format:
        ******** Essay number: 1 ************
        [Essay content here]

        ******** Essay number: 2 ************
        [Essay content here]

    Args:
        filepath: Path to the essay file
        essay_number: Essay number to extract (1-indexed)

    Returns:
        Essay text if found, None otherwise
    """
    essay = ""
    found_essay = False
    found_one = False

    marker = f"******** Essay number: {essay_number} ************"

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() == marker:
                    found_essay = True
                    found_one = True
                    continue

                if found_essay and line.startswith("******** Essay number: "):
                    found_essay = False
                    continue

                if found_essay:
                    essay += line

    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"ERROR: Failed to read {filepath}: {e}")
        return None

    if not found_one:
        return None

    return essay.strip()


def ensure_dir(directory: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory: Path to directory
    """
    directory.mkdir(parents=True, exist_ok=True)


def clear_file(filepath: Path) -> None:
    """
    Clear/delete a file if it exists.

    Args:
        filepath: Path to file
    """
    if filepath.exists():
        filepath.unlink()
