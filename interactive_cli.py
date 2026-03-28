"""
Interactive command-line tool that walks a non-expert user through
the decision tree to recommend a block cipher mode of operation.
"""

import json
import sys


# ─── Display Helpers ─────────────────────────────────────────────────────────

def clear_line():
    """Print a visual separator."""
    print("-" * 60)


def print_header():
    """Print the welcome banner."""
    print()
    print("=" * 60)
    print("  Block Cipher Mode of Operation — Selection Tool")
    print("=" * 60)
    print()
    print("  This tool helps you choose the right block cipher mode")
    print("  of operation based on your requirements.")
    print("  Answer the following questions. You can always choose")
    print("  \"I don't know\" if you're unsure.")
    print()
    clear_line()
    print()


def print_recommendation(names: list[str], full_names: dict, warning: str | None,
                         table_schemes: list[dict], column_labels: dict):
    """Display the final recommendation."""
    print()
    clear_line()

    if len(names) == 1:
        name = names[0]
        fn = full_names.get(name, "")
        print(f"  ✅ Recommended mode: {name} ({fn})")
    else:
        print(f"  📋 Top candidates (ranked):")
        for i, name in enumerate(names, 1):
            fn = full_names.get(name, "")
            print(f"     {i}. {name} ({fn})")

    if warning:
        print()
        print(f"  ⚠  {warning}")

    print()
    clear_line()

    # Show properties for each recommended scheme
    for name in names:
        scheme = next((s for s in table_schemes if s["name"] == name), None)
        if scheme:
            print()
            fn = full_names.get(name, "")
            print(f"  Properties of {name} ({fn}):")
            print(f"  ├─ Type:              {_friendly_val('mode_type', scheme['mode_type'])}")
            print(f"  ├─ Security:          {_friendly_val('security_level', scheme['security_level'])}")
            print(f"  ├─ Speed:             {_friendly_val('runtime_efficiency', scheme['runtime_efficiency'])}")
            print(f"  ├─ Parallel Encrypt:  {_bool_icon(scheme['parallel_encryption'])}")
            print(f"  ├─ Parallel Decrypt:  {_bool_icon(scheme['parallel_decryption'])}")
            print(f"  ├─ Random Access:     {_bool_icon(scheme['random_access_decryption'])}")
            print(f"  ├─ IV Required:       {_bool_icon(scheme['iv_required'])}")
            print(f"  ├─ Error Propagation: {_friendly_val('error_propagation', scheme['error_propagation'])}")
            print(f"  └─ Preprocessing:     {_bool_icon(scheme['preprocessing_possible'])}")
    print()


def _bool_icon(val: bool) -> str:
    return "Yes" if val else "No"


def _friendly_val(feature: str, val) -> str:
    """Convert a raw feature value to a friendly display string."""
    display = {
        "mode_type": {"block": "Block cipher", "stream": "Stream cipher"},
        "security_level": {
            "none": "None (insecure)",
            "IND-CPA": "IND-CPA (secure against chosen-plaintext attacks)",
            "IND-CCA+AUTH": "IND-CCA + Authentication (AEAD — confidentiality + integrity)",
        },
        "runtime_efficiency": {"fastest": "Fastest", "fast": "Fast"},
        "error_propagation": {
            "1_block": "1 block only",
            "2_blocks": "2 blocks (corrupted + next)",
            "all_fail": "Entire message rejected (auth tag fails)",
        },
    }
    return display.get(feature, {}).get(val, str(val))


# ─── Tree Traversal ──────────────────────────────────────────────────────────

def traverse_tree(node: dict, table_schemes: list[dict], column_labels: dict,
                  question_num: int = 1) -> tuple[list[str], dict, str | None]:
    """
    Walk through the decision tree interactively.

    Returns (recommendations, full_names, warning).
    """
    # Leaf node — return recommendation
    if node["type"] == "leaf":
        return node["recommendations"], node.get("full_names", {}), node.get("warning")

    # Question node — ask the user
    question_text = node["text"]
    children = {k: v for k, v in node["children"].items() if not k.startswith("_")}
    option_labels = list(children.keys())

    print(f"  Q{question_num}: {question_text}")
    print()

    for i, label in enumerate(option_labels, 1):
        print(f"    {i}. {label}")
    idk_num = len(option_labels) + 1
    print(f"    {idk_num}. I don't know")
    print()

    # Get user input
    while True:
        try:
            raw = input(f"  Your choice (1-{idk_num}): ").strip()
            choice = int(raw)
            if 1 <= choice <= idk_num:
                break
            print(f"  Please enter a number between 1 and {idk_num}.")
        except ValueError:
            print(f"  Please enter a number between 1 and {idk_num}.")
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            sys.exit(0)

    print()

    # "I don't know" — collect all reachable leaves
    if choice == idk_num:
        all_recs = []
        all_full_names = {}
        all_warnings = []

        for label, child_node in children.items():
            recs, fnames, warn = traverse_tree(
                child_node, table_schemes, column_labels, question_num + 1
            )
            for r in recs:
                if r not in all_recs:
                    all_recs.append(r)
            all_full_names.update(fnames)
            if warn:
                all_warnings.append(warn)

        warning = "; ".join(all_warnings) if all_warnings else None
        return all_recs, all_full_names, warning

    # Normal answer — traverse the chosen branch
    chosen_label = option_labels[choice - 1]
    child_node = children[chosen_label]
    return traverse_tree(child_node, table_schemes, column_labels, question_num + 1)


# ─── Full Comparison Table ───────────────────────────────────────────────────

def print_full_table(schemes: list[dict], column_labels: dict):
    """Print the full implementation usage table."""
    print()
    print("=" * 60)
    print("  Full Implementation Usage Comparison Table")
    print("=" * 60)
    print()

    # Header
    header = f"{'Mode':<6}"
    cols_to_show = [
        ("mode_type", 8),
        ("security_level", 16),
        ("runtime_efficiency", 8),
        ("parallel_encryption", 6),
        ("parallel_decryption", 6),
        ("random_access_decryption", 6),
        ("iv_required", 4),
        ("error_propagation", 12),
        ("preprocessing_possible", 6),
    ]
    short_labels = {
        "mode_type": "Type",
        "security_level": "Security",
        "runtime_efficiency": "Speed",
        "parallel_encryption": "P.Enc",
        "parallel_decryption": "P.Dec",
        "random_access_decryption": "R.Acc",
        "iv_required": "IV",
        "error_propagation": "Err.Prop",
        "preprocessing_possible": "Prepr",
    }

    header = f"  {'Mode':<6}"
    for col, width in cols_to_show:
        header += f" {short_labels[col]:<{width}}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    for s in schemes:
        row = f"  {s['name']:<6}"
        for col, width in cols_to_show:
            val = s[col]
            if isinstance(val, bool):
                display = "Y" if val else "N"
            else:
                display = str(val)
            row += f" {display:<{width}}"
        print(row)

    print()


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    # Load data
    try:
        with open("tree.json", "r") as f:
            tree_data = json.load(f)
        with open("table.json", "r") as f:
            table = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Run 'python decision_tree.py' first to generate tree.json.")
        sys.exit(1)

    tree = tree_data["tree"]
    schemes = table["schemes"]
    column_labels = table["column_labels"]

    # Welcome
    print_header()

    # Walk through the tree
    recs, full_names, warning = traverse_tree(tree, schemes, column_labels)

    # Show recommendation
    print_recommendation(recs, full_names, warning, schemes, column_labels)

    # Offer full table
    try:
        show_table = input("  Would you like to see the full comparison table? (y/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        show_table = "n"

    if show_table in ("y", "yes"):
        print_full_table(schemes, column_labels)

    print("  Thank you for using the Block Cipher Mode Selection Tool!")
    print()


if __name__ == "__main__":
    main()