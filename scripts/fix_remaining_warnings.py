#!/usr/bin/env python3
"""Fix remaining flake8 warnings: E712, W291, W293, F541"""

import re
from pathlib import Path


def fix_file(file_path):
    """Fix all warnings in a single file."""
    with open(file_path, "r") as f:
        content = f.read()

    original = content
    changes = []

    # Fix E712: comparison to True/False
    # Pattern 1: == True
    new_content = re.sub(
        r"(\s+if\s+)([^=\n]+?)\s*==\s*True(\s*:)",
        r"\1\2\3",
        content,
    )
    if new_content != content:
        changes.append("E712: == True")
        content = new_content

    # Pattern 2: == False
    new_content = re.sub(
        r"(\s+if\s+)([^=\n]+?)\s*==\s*False(\s*:)",
        r"\1not \2\3",
        content,
    )
    if new_content != content:
        changes.append("E712: == False")
        content = new_content

    # Fix W291/W293: trailing whitespace
    lines = content.split("\n")
    new_lines = [line.rstrip() for line in lines]
    new_content = "\n".join(new_lines)
    if new_content != content:
        changes.append("W291/W293: trailing whitespace")
        content = new_content

    # Fix F541: f-string without placeholders
    # Simple pattern: "text" or 'text' without {}
    new_content = re.sub(r'"([^"{]*)"', r'"\1"', content)
    new_content = re.sub(r"'([^'{]*)'", r"'\1'", new_content)
    if new_content != content:
        changes.append("F541: f-string placeholders")
        content = new_content

    if content != original:
        with open(file_path, "w") as f:
            f.write(content)
        return changes

    return []


def main():
    """Main function."""
    print("🔧 Fixing remaining flake8 warnings...")

    # Find all Python files
    python_files = []
    for pattern in ["app/**/*.py", "tests/**/*.py", "scripts/**/*.py"]:
        python_files.extend(Path(".").glob(pattern))

    fixed_files = 0
    total_changes = 0

    for file_path in python_files:
        changes = fix_file(file_path)
        if changes:
            fixed_files += 1
            total_changes += len(changes)
            print(f"✓ {file_path}: {', '.join(changes)}")

    print(f"\n✅ Fixed {total_changes} issues in {fixed_files} files!")


if __name__ == "__main__":
    main()
