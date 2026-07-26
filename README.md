# Almost Symmetric Games

This repository develops **incentive-preserving projections and certified
equilibrium computation for finite games with approximate symmetries**.

Exact game symmetries are useful for representation, equilibrium selection, and
computation, but they are brittle: small agent heterogeneity, estimated payoff
tables, or design perturbations destroy literal payoff invariance. The project
therefore measures symmetry at the level of **unilateral-deviation incentives**
rather than raw payoffs.

For a supplied group `G` of player/action relabelings, the code computes

- the strategic symmetry defect: maximum-pairwise-difference distance to the
  nearest exactly `G`-symmetric game;
- a nearest symmetric surrogate by sparse linear programming;
- an equivalent maximum-mean-cycle characterization;
- a certified critical-cycle witness and constructive orbit potentials;
- Reynolds/orbit averaging, a closed-form factor-two projection;
- symmetry-respecting zero-sum equilibria and a posteriori saddle-gap
  certificates; and
- orbit-compressed zero-sum solvers.

The current theorem stack proves that an `epsilon`-Nash equilibrium of a
surrogate at strategic distance `delta` is an `(epsilon + delta)`-Nash
equilibrium of the original game. Consequently, every finite game admits a
`G`-respecting `delta_G`-Nash equilibrium. The additive coefficient one is
asymptotically tight. Group averaging is always within factor two of the
optimal strategic projection, and an explicit family attains ratio

```text
2 - 2 / d^2
```

so this factor is also asymptotically tight.

## Repository layout

- `paper/main.tex`: AAAI-27 main manuscript.
- `paper/supplement.tex`: complete proofs and additional experimental details.
- `src/almost_symmetric/`: game, symmetry, projection, cycle, and zero-sum
  algorithms.
- `experiments/run_all.py`: deterministic experiment suite and figure generator.
- `experiments/sharpness.py`: exact Reynolds factor-two construction.
- `experiments/results/`: generated CSV tables and summary metrics.
- `experiments/figures/`: generated PDF/PNG figures, not versioned.
- `tests/`: unit, adversarial, and randomized theorem-regression tests.
- `scripts/check_submission.py`: page, font, metadata, and LaTeX-log checks.
- `notes/proof_notes.md`: detailed proof development.
- `notes/novelty_audit.md`: closest-work and claim-boundary audit.
- `.github/workflows/validate.yml`: clean-machine tests, reproduction, and PDF
  validation.

## Installation

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --no-build-isolation -e ".[dev]"
```

## Run tests

```bash
pytest
```

The adversarial cycle tests cover critical self-loops, parallel-edge
compression, global action orbits under player swaps, exact sharpness families,
and randomized agreement between the cycle and LP solvers.

## Reproduce experiments

Full deterministic sweep:

```bash
PYTHONPATH=src python -m experiments.run_all \
  --seed 17 \
  --replicates 20 \
  --sampling-replicates 40
```

Small CI smoke sweep:

```bash
PYTHONPATH=src python -m experiments.run_all --quick
```

The suite uses one CPU core, fixed seeds, NumPy/SciPy linear programming, and
small explicit games. No GPU is required.

## Build and validate the submission

The repository includes the official AAAI-27 author kit. From the repository
root, one command regenerates the experiments, builds both PDFs, and runs the
submission checks:

```bash
make -C paper check
```

To compile existing figures without rerunning experiments:

```bash
make -C paper
```

The checker verifies:

- technical content does not extend beyond page seven;
- the PDF uses US-letter pages;
- fonts are embedded and no Type 3 fonts are present;
- PDF author metadata remains anonymous;
- LaTeX reports no unresolved references, citations, or material overfull
  boxes.

## Current empirical checks

With seed 17, the committed deterministic studies report:

- cycle and LP defects agree to numerical precision;
- every critical-cycle witness is a closed walk whose mean certifies the defect;
- no equilibrium-transfer certificate violation in the perturbed zero-sum
  sweep;
- the largest random-perturbation Reynolds/optimal ratio is about `1.325`;
- the sharpness family matches `2 - 2 / d^2` and reaches `1.995` at `d=20`;
- raw payoff defect grows under strategically irrelevant shifts while strategic
  defect remains numerically zero;
- orbit reduction produces increasing runtime separation through 512 actions
  per player; and
- the finite-sample certificate covers every trial in the committed sweep.

These are synthetic theorem checks and diagnostics, not claims about large-scale
learned agents.

## Scope and limitations

The candidate relabeling group is supplied as semantic prior knowledge or as a
small hierarchy. Discovering approximate symmetries from scratch is outside the
first paper. In general-sum games, projection and transfer are tractable but Nash
equilibrium computation retains its usual hardness. The strategic defect
certifies incentives and exploitability, not welfare or equilibrium selection.
The implementation uses explicit normal-form tables; compact graphical,
polymatrix, stochastic, and extensive-form extensions remain future work.
