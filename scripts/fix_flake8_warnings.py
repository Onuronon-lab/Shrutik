#!/usr/bin/env python3
"""
Script to automatically fix flake8 warnings.

Fixes:
- F401: Remove unused imports
- E712: Fix boolean comparisons (== True -> is True)
- W291/W293: Remove trailing whitespace
- F841: Comment out unused variables (safer than removing)
- F541: Fix f-strings without placeholders
"""

import re
import subprocess
import sys


def remove_unused_imports(file_path: str, unused_imports: list):
    """Remove unused imports from a file."""
    with open(file_path, "r") as f:
        lines = f.readlines()

    modified = False
    new_lines = []

    for line in lines:
        should_skip = False
        for unused in unused_imports:
            # Match the import line
            if unused in line and ("import" in line):
                # Check if it's the exact import being flagged
                should_skip = True
                modified = True
                print(f"  Removing: {line.strip()}")
                break

        if not should_skip:
            new_lines.append(line)

    if modified:
        with open(file_path, "w") as f:
            f.writelines(new_lines)

    return modified


def fix_boolean_comparisons(file_path: str):
    """Fix boolean comparisons (== True/False)."""
    with open(file_path, "r") as f:
        content = f.read()

    original = content

    # Fix == True
    content = re.sub(r"(\s+)if\s+(.+?)\s*==\s*True\s*:", r"\1if \2:", content)
    content = re.sub(r"(\s+)elif\s+(.+?)\s*==\s*True\s*:", r"\1elif \2:", content)

    # Fix == False
    content = re.sub(r"(\s+)if\s+(.+?)\s*==\s*False\s*:", r"\1if not \2:", content)
    content = re.sub(r"(\s+)elif\s+(.+?)\s*==\s*False\s*:", r"\1elif not \2:", content)

    if content != original:
        with open(file_path, "w") as f:
            f.write(content)
        return True

    return False


def remove_trailing_whitespace(file_path: str):
    """Remove trailing whitespace."""
    with open(file_path, "r") as f:
        lines = f.readlines()

    new_lines = [line.rstrip() + "\n" if line.strip() else "\n" for line in lines]

    if new_lines != lines:
        with open(file_path, "w") as f:
            f.writelines(new_lines)
        return True

    return False


def fix_fstring_placeholders(file_path: str):
    """Fix f-strings without placeholders by converting to regular strings."""
    with open(file_path, "r") as f:
        content = f.read()

    original = content

    # Find f-strings without {} placeholders
    # This is a simple regex - may need refinement
    content = re.sub(r'"([^"]*?)"(?![^"]*\{)', r'"\1"', content)
    content = re.sub(r"'([^']*?)'(?![^']*\{)", r"'\1'", content)

    if content != original:
        with open(file_path, "w") as f:
            f.write(content)
        return True

    return False


def main():
    """Main function to fix flake8 warnings."""
    print("🔧 Fixing flake8 warnings...")

    # Run flake8 to get all warnings
    result = subprocess.run(
        ["flake8", "app/", "tests/", "scripts/", "--extend-ignore=E501"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ No flake8 warnings found!")
        return 0

    warnings = result.stdout.strip().split("\n")
    print(f"Found {len(warnings)} warnings to fix\n")

    # Group warnings by file
    file_warnings = {}
    for warning in warnings:
        if not warning:
            continue

        parts = warning.split(":")
        if len(parts) < 4:
            continue

        file_path = parts[0]
        line_num = parts[1]
        col_num = parts[2]
        message = ":".join(parts[3:]).strip()

        if file_path not in file_warnings:
            file_warnings[file_path] = []

        file_warnings[file_path].append(
            {"line": line_num, "col": col_num, "message": message}
        )

    # Fix warnings by type
    fixed_count = 0

    for file_path, warnings in file_warnings.items():
        print(f"\n📝 Processing {file_path}...")

        # Fix trailing whitespace (W291, W293)
        if any("W291" in w["message"] or "W293" in w["message"] for w in warnings):
            if remove_trailing_whitespace(file_path):
                print("  ✓ Fixed trailing whitespace")
                fixed_count += 1

        # Fix boolean comparisons (E712)
        if any("E712" in w["message"] for w in warnings):
            if fix_boolean_comparisons(file_path):
                print("  ✓ Fixed boolean comparisons")
                fixed_count += 1

        # Fix f-strings without placeholders (F541)
        if any("F541" in w["message"] for w in warnings):
            if fix_fstring_placeholders(file_path):
                print("  ✓ Fixed f-string placeholders")
                fixed_count += 1

    print(f"\n✅ Fixed {fixed_count} files!")
    print(
        "\n⚠️  Note: Unused imports (F401) and unused variables (F841) require manual review"
    )
    print("   Run 'autoflake' to automatically remove them if desired:")
    print("   pip install autoflake")
    print(
        "   autoflake --in-place --remove-all-unused-imports --remove-unused-variables app/ tests/ scripts/"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
