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
- symmetry-respecting Nash, correlated, and coarse-correlated equilibria;
- profile-orbit correlated-equilibrium programs for general-sum games;
- symmetry-respecting zero-sum equilibria and saddle-gap certificates;
- orbit-compressed zero-sum and correlated-equilibrium solvers; and
- confidence-calibrated selection of the most compressed candidate symmetry
  supported by a sampled payoff table.

The theorem stack proves that an `epsilon`-Nash, correlated, or
coarse-correlated equilibrium of a surrogate at strategic distance `delta`
transfers with additive violation at most `delta`. Consequently, every finite
game admits `G`-respecting `delta_G` versions of all three solution concepts.
The Nash coefficient one is asymptotically tight.

Group averaging is always within factor two of the optimal strategic
projection, and an explicit zero-sum family attains ratio

```text
2 - 2 / d
```

so this factor is also asymptotically tight. Correlation provides a separate
coordination resource: in the `n`-agent, `n`-role assignment game, independent
invariant play has welfare `n! / n**n`, while an invariant correlated
equilibrium has welfare one.

For a hierarchy of candidate groups, the statistical selector chooses the
smallest orbit representation whose empirical defect plus a common confidence
radius fits a target incentive budget. The same payoff-table event controls all
candidates, so post-selection does not require an additional multiplicity term.

## Repository layout

- `paper/main.tex`: AAAI-27 main manuscript.
- `paper/supplement.tex`: complete proofs and additional experimental details.
- `src/almost_symmetric/`: game, symmetry, projection, cycle, selection,
  zero-sum, and correlated-equilibrium algorithms.
- `experiments/run_all.py`: deterministic experiment suite and figure generator.
- `experiments/correlated_studies.py`: CE transfer, role assignment, and
  profile-orbit compression studies.
- `experiments/selection_study.py`: sampled-payoff hierarchy selection and
  certificate study.
- `experiments/sharpness.py`: exact zero-sum Reynolds factor-two construction.
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
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
```

## Run tests

```bash
pytest
```

The adversarial tests cover empty incentive graphs, critical self-loops,
parallel-edge compression, player-swapping symmetries, exact sharpness
families, CE/CCE transfer, statistical group selection, invariant profile
orbits, and randomized agreement between the cycle and LP solvers.

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
root, one command regenerates the experiments, builds the manuscript,
supplement, and reproducibility checklist, and runs the submission checks:

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

The deterministic studies verify that

- cycle and LP defects agree to numerical precision;
- every critical-cycle witness is a closed walk whose mean certifies the defect;
- transferred Nash, CE, and CCE solutions satisfy their strategic-distance
  certificates;
- direct invariant approximate-CE optimization can improve welfare while
  retaining the same incentive budget;
- the role-assignment CE LP recovers welfare one, matching the analytic
  construction;
- the zero-sum sharpness family matches `2 - 2 / d`;
- raw payoff defect grows under strategically irrelevant shifts while strategic
  defect remains numerically zero;
- orbit reduction produces increasing separation in both zero-sum strategy
  programs and correlated joint-distribution variables;
- the finite-sample equilibrium certificate covers every trial; and
- the hierarchy selector certifies the true selected defect and regret in every
  committed trial and reaches the population-oracle compression at the largest
  sample sizes.

These are synthetic theorem checks and diagnostics, not claims about large-scale
learned agents.

## Scope and limitations

The candidate relabeling group is supplied as semantic prior knowledge or as a
small hierarchy. Discovering approximate symmetries from scratch is outside the
first paper. In general-sum games, projection and CE/CCE optimization are
tractable, but Nash equilibrium computation retains its usual hardness. The
strategic defect certifies incentives and exploitability, not welfare or
equilibrium selection unless an explicit selection objective is imposed. The
implementation uses explicit normal-form tables; compact graphical, polymatrix,
stochastic, and extensive-form extensions remain future work.
