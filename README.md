# Almost Symmetric Games

This repository develops **incentive-preserving projections and certified
equilibrium computation for finite games with approximate symmetries**.

Exact game symmetries are useful for representation, equilibrium selection, and
computation, but they are brittle: small agent heterogeneity, estimated payoff
tables, or design perturbations destroy literal payoff invariance. The project
therefore measures symmetry at the level of **unilateral-deviation incentives**
rather than raw payoffs.

For a supplied group `G` of player/action relabelings, the code computes

- the strategic symmetry defect (maximum-pairwise-difference distance to the
  nearest exactly `G`-symmetric game);
- a nearest symmetric surrogate by linear programming;
- an equivalent maximum-mean-cycle characterization and a local witness cycle;
- Reynolds/orbit averaging, a closed-form factor-two projection;
- symmetry-respecting zero-sum equilibria and a posteriori saddle-gap
  certificates; and
- orbit-compressed zero-sum solvers.

The current theorem stack proves that an `epsilon`-Nash equilibrium of a
surrogate at strategic distance `delta` is an `(epsilon + delta)`-Nash
equilibrium of the original game. Consequently, every finite game admits a
`G`-respecting `delta_G`-Nash equilibrium, where `delta_G` is its optimal
strategic symmetry defect. The additive constant is tight.

## Repository layout

- `paper/main.tex`: AAAI-27 main manuscript.
- `paper/supplement.tex`: complete proofs and additional experiments.
- `src/almost_symmetric/`: game, symmetry, projection, cycle, and zero-sum
  algorithms.
- `experiments/run_all.py`: deterministic experiment suite and figure generator.
- `experiments/results/`: generated CSV tables and summary metrics.
- `experiments/figures/`: generated PDF/PNG figures (regenerated locally and not versioned).
- `tests/`: unit and theorem-regression tests.
- `notes/proof_notes.md`: detailed proof development and audit checklist.

## Installation

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Reproduce all experiments

```bash
PYTHONPATH=src python experiments/run_all.py
```

The experiment suite uses one CPU core, fixed seeds, NumPy/SciPy linear
programming, and small explicit games. No GPU is required.

## Run tests

```bash
PYTHONPATH=src pytest
```

## Build the paper

The repository includes the official AAAI-27 author kit in
`AAAI_AuthorKit27/`. From the repository root:

```bash
make -C paper
```

The Makefile first regenerates all result tables and figures, then produces `paper/main.pdf` and `paper/supplement.pdf`.

## Current empirical checks

With seed 17, the checked-in experiment run reports:

- cycle and LP defects agree to within `1.8e-15`;
- no equilibrium-transfer certificate violation across 140 perturbed zero-sum
  games;
- the largest observed Reynolds/optimal defect ratio is `1.325`, below the
  proved factor two;
- raw payoff defect reaches `8.535` under strategically irrelevant shifts while
  strategic defect remains numerically zero; and
- orbit compression gives over `20x` speedup on the largest 512-by-512 exact
  duplicate game in the suite.

These are deterministic synthetic validations of the theory, not claims about
large-scale learned agents.

## Scope and limitations

The candidate relabeling group is supplied as semantic prior knowledge or as a
small hierarchy. Discovering approximate symmetries from scratch is intentionally
left outside the first paper. In general-sum games, the results guarantee the
existence and validity of symmetry-respecting approximate equilibria but do not
remove the usual hardness of Nash equilibrium computation. The strategic defect
certifies incentives/exploitability, not welfare; exact symmetry can still make
symmetry-respecting equilibrium selection inefficient.
