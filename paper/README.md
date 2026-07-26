# AAAI Paper Draft

The manuscript is organized as a modular AAAI-27 submission:

```text
main.tex
sections/
    01_introduction_related.tex
    02_preliminaries.tex
    03_projection_transfer.tex
    04_orbit_averaging.tex
    05_zero_sum_sampling.tex
    06_experiments.tex
    07_discussion.tex
supplement.tex
references.bib
```

## Build

The repository includes the AAAI-27 author kit one directory above. From this directory, run:

```bash
make
```

This requires `latexmk`, `pdflatex`, and `bibtex`. To compile separately:

```bash
make main
make supplement
```

Generated experiment figures must already exist in `../experiments/figures/`. They can be regenerated from the repository root with:

```bash
python experiments/run_all.py --seed 17 --replicates 10
```

## Current manuscript claims

The draft develops:

1. an incentive-based strategic symmetry defect that quotients out nonstrategic payoff shifts;
2. a sparse exact projection LP;
3. a maximum-mean-cycle characterization and critical-cycle obstruction witness for the unrestricted projection;
4. additive equilibrium transfer and an asymptotically tight invariant-equilibrium guarantee;
5. a factor-two guarantee for Reynolds/orbit averaging;
6. structured zero-sum projection and direct invariant saddle-gap programs;
7. orbit-reduced computation and finite-sample payoff certificates;
8. six lightweight validation families, including heterogeneous role assignment.

Detailed proofs are in `supplement.tex` and audit notes are in `../notes/`.

## Submission-readiness checklist

The source is a substantial research draft, but the following checks remain before submission:

- compile on a clean system with the official AAAI-27 toolchain;
- confirm seven-page main-content compliance after bibliography and figure placement settle;
- inspect all fonts, overfull boxes, labels, and anonymous metadata;
- complete a formal novelty audit against exact game symmetries, near-potential games, game abstraction, and difference-constraint literature;
- independently verify the maximum-mean-cycle theorem and its sign/orientation conventions;
- replace provisional abbreviated bibliography author lists with complete archival metadata;
- decide which proof details belong in the main paper versus the allowed supplementary material under the final AAAI-27 policy.
