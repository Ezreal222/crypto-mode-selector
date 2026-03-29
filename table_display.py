"""
Prints the implementation usage table from table.json.
"""

import json


def main():
    with open("table.json", "r") as f:
        table = json.load(f)

    schemes = table["schemes"]
    col_labels = table["column_labels"]
    col_descs = table["column_descriptions"]

    print()
    print("=" * 80)
    print(f"  Implementation Usage Table: {table['primitive']}")
    print(f"  {table['description']}")
    print("=" * 80)
    print()

    # Print column descriptions
    print("  Column Definitions:")
    for col in table["columns"]:
        print(f"    • {col_labels[col]}: {col_descs[col]}")
    print()

    # Print table
    # Define column widths
    col_config = [
        ("name", "Mode", 6),
        ("mode_type", "Type", 8),
        ("runtime_efficiency", "Speed", 8),
        ("security_level", "Security", 16),
        ("random_access_decryption", "R.Access", 8),
        ("parallel_encryption", "P.Enc", 6),
        ("parallel_decryption", "P.Dec", 6),
        ("iv_required", "IV", 4),
        ("error_propagation", "Err.Prop", 10),
        ("preprocessing_possible", "Preproc", 8),
    ]

    # Header
    header = "  "
    for key, label, width in col_config:
        header += f"{label:<{width}} "
    print(header)
    print("  " + "-" * (len(header) - 2))

    # Rows
    for s in schemes:
        row = "  "
        for key, label, width in col_config:
            val = s[key]
            if isinstance(val, bool):
                display = "Yes" if val else "No"
            else:
                display = str(val)
            row += f"{display:<{width}} "
        print(row)

    print()
    print(f"  Total schemes: {len(schemes)}")
    print(f"  Total features: {len(table['columns'])}")
    print(f"  New rows vs. lecture 5 (Slide 34): CFB, GCM (separated from CTR)")
    print(f"  New columns vs. lecture 5 (Slide 34): parallel_encryption, parallel_decryption,")
    print(f"    iv_required, error_propagation, preprocessing_possible")
    print()


if __name__ == "__main__":
    main()