"""
Builds a decision tree from the implementation usage table (table.json)
using ID3 algorithm (information gain via entropy).
Saves the generated tree to tree.json.
"""

import json
import math
from collections import Counter


# ─── Plain-English question mapping ──────────────────────────────────────────
# Each feature maps to a question dict with:
#   "text" = the question for the user
#   "options" = mapping from raw value → user-friendly label

QUESTION_MAP = {
    "security_level": {
        "text": "What level of security do you need?",
        "options": {
            "IND-CCA+AUTH": "Authenticated encryption (confidentiality + integrity + tamper detection)",
            "IND-CPA": "Standard encryption (confidentiality only, secure against chosen-plaintext attacks)",
            "none": "No security needed (just encoding / testing purposes)",
        },
    },
    "parallel_encryption": {
        "text": "Do you need to encrypt data in parallel (e.g., on multi-core hardware or GPUs)?",
        "options": {True: "Yes", False: "No"},
    },
    "parallel_decryption": {
        "text": "Do you need to decrypt data in parallel?",
        "options": {True: "Yes", False: "No"},
    },
    "random_access_decryption": {
        "text": "Do you need to decrypt individual blocks without processing the entire message (random access)?",
        "options": {True: "Yes", False: "No"},
    },
    "preprocessing_possible": {
        "text": "Do you want to pre-compute the keystream before the actual plaintext is available?",
        "options": {True: "Yes", False: "No"},
    },
    "mode_type": {
        "text": "What type of cipher operation do you prefer?",
        "options": {
            "block": "Block cipher (processes fixed-size blocks)",
            "stream": "Stream cipher (processes data as a continuous stream)",
        },
    },
    "error_propagation": {
        "text": "If a single ciphertext block is corrupted during transmission, what error behavior is acceptable?",
        "options": {
            "1_block": "Only the corrupted block is affected (minimal propagation)",
            "2_blocks": "The corrupted block and the next block are affected",
            "all_fail": "The entire message is rejected (authentication fails)",
        },
    },
    "iv_required": {
        "text": "Is it acceptable for your system to generate and transmit a random initialization vector (IV) with each message?",
        "options": {True: "Yes", False: "No"},
    },
    "runtime_efficiency": {
        "text": "How important is raw encryption/decryption speed?",
        "options": {
            "fastest": "Maximum speed (need the fastest possible)",
            "fast": "Fast is fine (don't need absolute fastest)",
        },
    },
}


# ─── Entropy & Information Gain ──────────────────────────────────────────────

def entropy(labels: list) -> float:
    """Calculate Shannon entropy of a list of labels."""
    n = len(labels)
    if n == 0:
        return 0.0
    counts = Counter(labels)
    ent = 0.0
    for count in counts.values():
        p = count / n
        if p > 0:
            ent -= p * math.log2(p)
    return ent


def information_gain(schemes: list[dict], feature: str) -> float:
    """Calculate information gain of splitting on a given feature."""
    labels = [s["name"] for s in schemes]
    total_entropy = entropy(labels)

    # Group schemes by feature value
    groups = {}
    for s in schemes:
        val = s[feature]
        # Convert booleans to strings for consistent keying
        key = str(val)
        if key not in groups:
            groups[key] = []
        groups[key].append(s["name"])

    # Weighted entropy after split
    n = len(schemes)
    weighted_entropy = 0.0
    for group_labels in groups.values():
        weight = len(group_labels) / n
        weighted_entropy += weight * entropy(group_labels)

    return total_entropy - weighted_entropy


# ─── Tree Building (ID3) ─────────────────────────────────────────────────────

def build_tree(schemes: list[dict], features: list[str], depth: int = 0) -> dict:
    """
    Recursively build a decision tree using ID3.

    Returns a dict:
      - Leaf: {"type": "leaf", "recommendations": [...], "warning": "..."}
      - Internal: {"type": "question", "feature": "...", "text": "...",
                    "children": { "value_label": subtree, ... }}
    """
    scheme_names = [s["name"] for s in schemes]

    # Base case 1: only one scheme left (or all same)
    if len(set(scheme_names)) == 1:
        return _make_leaf(schemes)

    # Base case 2: no features left to split on
    if not features:
        return _make_leaf(schemes)

    # Base case 3: all remaining schemes have identical values for all remaining features
    all_same = True
    for f in features:
        vals = set(str(s[f]) for s in schemes)
        if len(vals) > 1:
            all_same = False
            break
    if all_same:
        return _make_leaf(schemes)

    # Find the feature with the highest information gain
    best_feature = None
    best_gain = -1.0
    for f in features:
        gain = information_gain(schemes, f)
        if gain > best_gain:
            best_gain = gain
            best_feature = f

    # If no gain from any feature, make a leaf
    if best_gain <= 0:
        return _make_leaf(schemes)

    # Split on the best feature
    remaining_features = [f for f in features if f != best_feature]

    # Group schemes by feature value
    groups = {}
    for s in schemes:
        val = s[best_feature]
        key = str(val)  # normalize booleans
        if key not in groups:
            groups[key] = []
        groups[key].append(s)

    # Build children
    children = {}
    qmap = QUESTION_MAP.get(best_feature, {})
    options_map = qmap.get("options", {})

    for raw_val, group_schemes in groups.items():
        # Try to find a user-friendly label
        # Need to convert raw_val back to its original type for lookup
        lookup_val = _parse_value(raw_val)
        label = options_map.get(lookup_val, options_map.get(raw_val, raw_val))

        children[label] = build_tree(group_schemes, remaining_features, depth + 1)
        # Store the raw value for evaluation purposes
        children[label]["_raw_value"] = raw_val

    question_text = qmap.get("text", f"What is the value of '{best_feature}'?")

    return {
        "type": "question",
        "feature": best_feature,
        "text": question_text,
        "children": children,
        "depth": depth,
    }


def _make_leaf(schemes: list[dict]) -> dict:
    """Create a leaf node with recommendations."""
    names = list(dict.fromkeys(s["name"] for s in schemes))  # preserve order, dedupe
    full_names = {s["name"]: s["full_name"] for s in schemes}

    warning = None
    if "ECB" in names and len(names) == 1:
        warning = (
            "WARNING: ECB is insecure! It leaks block equality patterns. "
            "Only use for testing or non-sensitive data."
        )

    return {
        "type": "leaf",
        "recommendations": names,
        "full_names": full_names,
        "warning": warning,
    }


def _parse_value(s: str):
    """Convert string back to original type (bool, etc.)."""
    if s == "True":
        return True
    if s == "False":
        return False
    return s


# ─── Tree Printing ───────────────────────────────────────────────────────────

def print_tree(node: dict, indent: int = 0):
    """Pretty-print the decision tree to console."""
    prefix = "  " * indent

    if node["type"] == "leaf":
        recs = node["recommendations"]
        if len(recs) == 1:
            print(f"{prefix}→ Recommend: {recs[0]} ({node['full_names'].get(recs[0], '')})")
        else:
            print(f"{prefix}→ Candidates: {', '.join(recs)}")
        if node.get("warning"):
            print(f"{prefix}  ⚠ {node['warning']}")
    else:
        print(f"{prefix}Q: {node['text']}  [feature: {node['feature']}]")
        for label, child in node["children"].items():
            if label.startswith("_"):
                continue
            print(f"{prefix}  ├─ \"{label}\"")
            print_tree(child, indent + 2)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    # Load table
    with open("table.json", "r") as f:
        table = json.load(f)

    schemes = table["schemes"]
    features = table["columns"]

    print("=" * 60)
    print("Building decision tree from implementation usage table...")
    print(f"  Schemes: {[s['name'] for s in schemes]}")
    print(f"  Features: {features}")
    print("=" * 60)
    print()

    # Build tree
    tree = build_tree(schemes, features)

    # Print tree
    print("Generated Decision Tree:")
    print("-" * 40)
    print_tree(tree)
    print()

    # Save tree to JSON
    output = {
        "primitive": table["primitive"],
        "tree": tree,
        "question_map": QUESTION_MAP,
    }
    with open("tree.json", "w") as f:
        json.dump(output, f, indent=2, default=str)

    print("Decision tree saved to tree.json")
    print()

    # Print feature selection order (for the presentation)
    print("Feature split order (by information gain):")
    _print_split_order(tree, level=1)


def _print_split_order(node: dict, level: int):
    """Print the order in which features are used for splitting."""
    if node["type"] == "leaf":
        return
    print(f"  Level {level}: {node['feature']} — \"{node['text']}\"")
    for label, child in node["children"].items():
        if isinstance(child, dict) and child.get("type") == "question":
            _print_split_order(child, level + 1)


if __name__ == "__main__":
    main()