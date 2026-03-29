# crypto-mode-selector

An interactive decision-tree tool that helps non-expert users select the optimal block cipher mode of operation (ECB, CBC, OFB, CTR, CFB, GCM) based on their security and performance requirements.

## Project Overview

This project is part of NYU CS6903 Applied Cryptography (Project 2.1). It:

1. Defines an **implementation usage table** comparing 6 block cipher modes across 9 feature dimensions (extending the lecture table with new rows and columns).
2. Builds a **decision tree** using the ID3 algorithm (information gain / entropy) to determine the optimal question ordering.
3. Provides an **interactive CLI** that walks non-expert users through plain-English questions to recommend a mode.
4. **Evaluates** the decision tree's accuracy against a random baseline.

## Requirements

- Python 3.10+
- No external libraries required (stdlib only)

## Quick Start

```bash
# 1. Generate the decision tree from the table
python decision_tree.py

# 2. Run the interactive recommendation tool
python interactive_cli.py

# 3. Run the evaluation experiments
python evaluate.py

# (Optional) View the implementation usage table
python table_display.py
```

## Implementation Usage Table

Based on Lecture 5, Slide 34, extended with new rows (CFB, GCM) and new columns.

| Mode | Type   | Speed   | Security     | R.Access | P.Enc | P.Dec | IV  | Err.Prop | Preproc |
| ---- | ------ | ------- | ------------ | -------- | ----- | ----- | --- | -------- | ------- |
| ECB  | block  | fastest | none         | Yes      | Yes   | Yes   | No  | 1 block  | No      |
| CBC  | block  | fast    | IND-CPA      | No       | No    | Yes   | Yes | 2 blocks | No      |
| OFB  | stream | fast    | IND-CPA      | No       | No    | No    | Yes | 1 block  | Yes     |
| CTR  | stream | fastest | IND-CPA      | Yes      | Yes   | Yes   | Yes | 1 block  | Yes     |
| CFB  | stream | fast    | IND-CPA      | No       | No    | Yes   | Yes | 2 blocks | No      |
| GCM  | stream | fastest | IND-CCA+AUTH | Yes      | Yes   | Yes   | Yes | all fail | Yes     |

### Extensions vs. Lecture Table (Slide 34)

- **New rows:** CFB (Cipher Feedback), GCM (separated from CTR grouping in lecture)
- **New columns:** Parallelizable Encryption, Parallelizable Decryption, IV Required, Error Propagation Scope, Keystream Preprocessing Possible

## Decision Tree Algorithm

The tree is built using the **ID3 algorithm**:

1. For each unused feature, compute the **information gain** (entropy of the current set minus the weighted entropy after splitting on that feature).
2. Split on the feature with the **highest information gain** — this produces the most discriminating question.
3. Recurse on each branch until all schemes in a branch are identical (leaf node).

The generated tree has a maximum depth of 3 questions and correctly identifies all 6 modes:

```
Q1: Error propagation?
├── 1 block → Q2: IV required?
│   ├── No  → ECB ⚠
│   └── Yes → Q3: Parallel decryption?
│       ├── No  → OFB
│       └── Yes → CTR
├── 2 blocks → Q2: Block or stream?
│   ├── Block  → CBC
│   └── Stream → CFB
└── All fail → GCM
```

## Sample Interaction

```
============================================================
  Block Cipher Mode of Operation — Selection Tool
============================================================
  This tool helps you choose the right block cipher mode
  of operation based on your requirements.
  Answer the following questions. You can always choose
  "I don't know" if you're unsure.
------------------------------------------------------------
  Q1: If a single ciphertext block is corrupted during transmission,
      what error behavior is acceptable?
    1. Only the corrupted block is affected (minimal propagation)
    2. The corrupted block and the next block are affected
    3. The entire message is rejected (authentication fails)
    4. I don't know
  Your choice (1-4): 1

  Q2: What type of cipher operation do you prefer?
    1. Block cipher (processes fixed-size blocks)
    2. Stream cipher (processes data as a continuous stream)
    3. I don't know
  Your choice (1-3): 2

  Q3: How important is raw encryption/decryption speed?
    1. Fast is fine (don't need absolute fastest)
    2. Maximum speed (need the fastest possible)
    3. I don't know
  Your choice (1-3): 1
------------------------------------------------------------
  ✅ Recommended mode: OFB (Output Feedback)
------------------------------------------------------------
  Properties of OFB (Output Feedback):
  ├─ Type:              Stream cipher
  ├─ Security:          IND-CPA (secure against chosen-plaintext attacks)
  ├─ Speed:             Fast
  ├─ Parallel Encrypt:  No
  ├─ Parallel Decrypt:  No
  ├─ Random Access:     No
  ├─ IV Required:       Yes
  ├─ Error Propagation: 1 block only
  └─ Preprocessing:     Yes

  Would you like to see the full comparison table? (y/n): n
  Thank you for using the Block Cipher Mode Selection Tool!
```

## Evaluation Results

The decision tree was evaluated across three experiments (1000 trials each):

| Experiment                                | Metric           | Result             |
| ----------------------------------------- | ---------------- | ------------------ |
| A: Perfect Knowledge                      | Accuracy         | 100.0% (1000/1000) |
| B: Partial Knowledge (30% "I don't know") | Top-1 Accuracy   | 67.0%              |
| B: Partial Knowledge (30% "I don't know") | Top-3 Accuracy   | 96.2%              |
| B: Partial Knowledge (30% "I don't know") | In-list Accuracy | 100.0%             |
| C: Random Baseline                        | Accuracy         | 16.1%              |

**Decision tree vs. random baseline: +83.9% improvement, roughly 6× better than random guessing**

- **Experiment A:** User answers every question correctly → tree always finds the right mode.
- **Experiment B:** User answers "I don't know" 30% of the time → correct mode is always in the candidate list, and ranked first 67% of the time.
- **Experiment C:** Randomly guessing a mode (no questions asked) → ~16.7% accuracy (1/6 schemes), serving as the baseline to show the decision tree provides meaningful value.
