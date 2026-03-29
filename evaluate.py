"""
Evaluates the decision tree's accuracy at recommending the correct
block cipher mode of operation.

Three experiments:
  A) Perfect knowledge — user answers all questions correctly
  B) Partial knowledge — user answers "I don't know" with probability 0.3
  C) Comparison with random baseline (1/num_schemes)
"""

import json
import random
import sys
from collections import defaultdict


# ─── Tree Traversal ──────────────────────────────

def simulate_perfect(scheme: dict, node: dict) -> list[str]:
    """
    Traverse the tree answering every question with the scheme's actual value.
    Returns list of recommended scheme names.
    """
    if node["type"] == "leaf":
        return node["recommendations"]

    feature = node["feature"]
    scheme_val = str(scheme[feature])

    # Find which child branch matches this scheme's value
    children = {k: v for k, v in node["children"].items() if not k.startswith("_")}

    for label, child_node in children.items():
        raw_val = child_node.get("_raw_value", "")
        if raw_val == scheme_val:
            return simulate_perfect(scheme, child_node)

    # If no branch matched (shouldn't happen with correct table), return all leaves
    return _collect_all_leaves(node)


def simulate_with_unknowns(scheme: dict, node: dict, unknown_prob: float = 0.3) -> list[str]:
    """
    Traverse the tree, answering "I don't know" with probability unknown_prob,
    otherwise answering correctly.
    Returns list of recommended scheme names.
    """
    if node["type"] == "leaf":
        return node["recommendations"]

    feature = node["feature"]
    scheme_val = str(scheme[feature])
    children = {k: v for k, v in node["children"].items() if not k.startswith("_")}

    # Decide: answer correctly or "I don't know"
    if random.random() < unknown_prob:
        # "I don't know" — collect all reachable leaves
        all_recs = []
        for label, child_node in children.items():
            recs = simulate_with_unknowns(scheme, child_node, unknown_prob)
            for r in recs:
                if r not in all_recs:
                    all_recs.append(r)
        return all_recs
    else:
        # Answer correctly
        for label, child_node in children.items():
            raw_val = child_node.get("_raw_value", "")
            if raw_val == scheme_val:
                return simulate_with_unknowns(scheme, child_node, unknown_prob)

        # Fallback
        return _collect_all_leaves(node)


def _collect_all_leaves(node: dict) -> list[str]:
    """Collect all recommendation names reachable from a node."""
    if node["type"] == "leaf":
        return node["recommendations"]

    all_recs = []
    children = {k: v for k, v in node["children"].items() if not k.startswith("_")}
    for label, child_node in children.items():
        recs = _collect_all_leaves(child_node)
        for r in recs:
            if r not in all_recs:
                all_recs.append(r)
    return all_recs


# ─── Experiments ─────────────────────────────────────────────────────────────

def experiment_a(schemes: list[dict], tree: dict, n_trials: int = 1000) -> dict:
    """
    Experiment A: Perfect Knowledge.
    For each trial, pick a random scheme, simulate perfect answers,
    check if the tree returns the correct scheme.
    """
    correct = 0
    per_scheme = defaultdict(lambda: {"correct": 0, "total": 0})

    for _ in range(n_trials):
        target = random.choice(schemes)
        recs = simulate_perfect(target, tree)
        is_correct = target["name"] in recs and len(recs) == 1

        if is_correct:
            correct += 1
        per_scheme[target["name"]]["total"] += 1
        per_scheme[target["name"]]["correct"] += int(is_correct)

    return {
        "name": "Experiment A: Perfect Knowledge",
        "total": n_trials,
        "correct": correct,
        "accuracy": correct / n_trials,
        "per_scheme": dict(per_scheme),
    }


def experiment_b(schemes: list[dict], tree: dict, n_trials: int = 1000,
                 unknown_prob: float = 0.3) -> dict:
    """
    Experiment B: Partial Knowledge.
    User answers "I don't know" with probability unknown_prob.
    Measure top-1 accuracy and top-3 accuracy.
    """
    top1_correct = 0
    top3_correct = 0
    in_list = 0

    for _ in range(n_trials):
        target = random.choice(schemes)
        recs = simulate_with_unknowns(target, tree, unknown_prob)

        # Top-1: is the target the sole recommendation?
        if len(recs) >= 1 and recs[0] == target["name"]:
            top1_correct += 1

        # Top-3: is the target in the first 3 recommendations?
        if target["name"] in recs[:3]:
            top3_correct += 1

        # In list at all?
        if target["name"] in recs:
            in_list += 1

    return {
        "name": f"Experiment B: Partial Knowledge (unknown_prob={unknown_prob})",
        "total": n_trials,
        "top1_correct": top1_correct,
        "top1_accuracy": top1_correct / n_trials,
        "top3_correct": top3_correct,
        "top3_accuracy": top3_correct / n_trials,
        "in_list": in_list,
        "in_list_accuracy": in_list / n_trials,
    }


def experiment_c(schemes: list[dict], n_trials: int = 1000) -> dict:
    """
    Experiment C: Random Baseline.
    Pick a scheme uniformly at random.
    """
    n_schemes = len(schemes)
    correct = 0
    for _ in range(n_trials):
        target = random.choice(schemes)
        guess = random.choice(schemes)
        if target["name"] == guess["name"]:
            correct += 1

    return {
        "name": "Experiment C: Random Baseline",
        "total": n_trials,
        "correct": correct,
        "accuracy": correct / n_trials,
        "expected": 1.0 / n_schemes,
    }


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
    n_trials = 1000

    random.seed(42)  # reproducible results

    print()
    print("=" * 60)
    print("  Decision Tree Evaluation")
    print(f"  Primitive: {table['primitive']}")
    print(f"  Schemes: {[s['name'] for s in schemes]}")
    print(f"  Trials per experiment: {n_trials}")
    print("=" * 60)
    print()

    # Run experiments
    result_a = experiment_a(schemes, tree, n_trials)
    result_b = experiment_b(schemes, tree, n_trials, unknown_prob=0.3)
    result_c = experiment_c(schemes, n_trials)

    # Print results
    print(f"  {result_a['name']}")
    print(f"    Accuracy: {result_a['accuracy']*100:.1f}% ({result_a['correct']}/{result_a['total']})")
    print(f"    Per-scheme breakdown:")
    for sname, stats in sorted(result_a["per_scheme"].items()):
        acc = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"      {sname:<6}: {acc:.0f}% ({stats['correct']}/{stats['total']})")
    print()

    print(f"  {result_b['name']}")
    print(f"    Top-1 Accuracy: {result_b['top1_accuracy']*100:.1f}% ({result_b['top1_correct']}/{result_b['total']})")
    print(f"    Top-3 Accuracy: {result_b['top3_accuracy']*100:.1f}% ({result_b['top3_correct']}/{result_b['total']})")
    print(f"    In-list:        {result_b['in_list_accuracy']*100:.1f}% ({result_b['in_list']}/{result_b['total']})")
    print()

    print(f"  {result_c['name']}")
    print(f"    Accuracy: {result_c['accuracy']*100:.1f}% ({result_c['correct']}/{result_c['total']})")
    print(f"    Expected: {result_c['expected']*100:.1f}% (1/{len(schemes)} schemes)")
    print()

    # Comparison
    improvement = result_a["accuracy"] - result_c["accuracy"]
    print("  Comparison:")
    print(f"    Decision Tree (perfect):   {result_a['accuracy']*100:.1f}%")
    print(f"    Decision Tree (partial):   {result_b['top1_accuracy']*100:.1f}% (top-1)")
    print(f"    Random Baseline:           {result_c['accuracy']*100:.1f}%")
    print(f"    Improvement over random:   +{improvement*100:.1f}%")
    print()

    # Save results
    all_results = {
        "experiment_a": result_a,
        "experiment_b": result_b,
        "experiment_c": result_c,
        "improvement_over_random": improvement,
    }
    with open("evaluation_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    print("  Results saved to evaluation_results.json")
    print()


if __name__ == "__main__":
    main()