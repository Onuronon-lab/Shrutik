#!/usr/bin/env python3
"""Fix all E712 boolean comparison warnings."""

import re
from pathlib import Path


def fix_e712_in_file(file_path):
    """Fix E712 warnings in a file."""
    with open(file_path, "r") as f:
        content = f.read()

    original = content

    # Fix filter() with == True/False (SQLAlchemy style)
    content = re.sub(
        r"\.filter\(([^)]+?)\s+==\s+True\)",
        r".filter(\1.is_(True))",
        content,
    )
    content = re.sub(
        r"\.filter\(([^)]+?)\s+==\s+False\)",
        r".filter(\1.is_(False))",
        content,
    )

    # Fix if statements with == True
    content = re.sub(
        r"(\s+if\s+)([a-zA-Z_][a-zA-Z0-9_\.]*)\s+==\s+True:",
        r"\1\2:",
        content,
    )

    # Fix if statements with == False
    content = re.sub(
        r"(\s+if\s+)([a-zA-Z_][a-zA-Z0-9_\.]*)\s+==\s+False:",
        r"\1not \2:",
        content,
    )

    # Fix elif statements with == True
    content = re.sub(
        r"(\s+elif\s+)([a-zA-Z_][a-zA-Z0-9_\.]*)\s+==\s+True:",
        r"\1\2:",
        content,
    )

    # Fix elif statements with == False
    content = re.sub(
        r"(\s+elif\s+)([a-zA-Z_][a-zA-Z0-9_\.]*)\s+==\s+False:",
        r"\1not \2:",
        content,
    )

    if content != original:
        with open(file_path, "w") as f:
            f.write(content)
        return True

    return False


def main():
    """Main function."""
    print("🔧 Fixing E712 boolean comparison warnings...")

    # Find all Python files
    python_files = []
    for pattern in ["app/**/*.py", "tests/**/*.py", "scripts/**/*.py"]:
        python_files.extend(Path(".").glob(pattern))

    fixed_count = 0

    for file_path in python_files:
        if fix_e712_in_file(file_path):
            fixed_count += 1
            print(f"✓ Fixed {file_path}")

    print(f"\n✅ Fixed {fixed_count} files!")


if __name__ == "__main__":
    main()
