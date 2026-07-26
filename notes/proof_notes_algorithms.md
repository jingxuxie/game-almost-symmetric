# Algorithm and Reproducibility Notes

This file documents the algorithms behind the manuscript and the exact relationship between implementation outputs and theoretical claims.

## 1. Data model

`NormalFormGame.payoffs` has shape

```text
(n_players, action_count_player_0, ..., action_count_player_{n-1})
```

A `Relabeling` stores:

- `player_perm[i]`: the destination of source player `i`;
- `action_perms[i][a]`: the destination action of source action `a`.

The implementation validates that every action map bijects onto the target player's action set. A candidate group is supplied by generators; no full group enumeration is needed for the main algorithms.

## 2. Orbit construction

Two orbit systems are used.

### Action orbits

The disjoint union of all player-action pairs is indexed by offsets. Generator edges are joined with union--find. A symmetry-respecting mixed profile assigns equal probability to coordinates in the same global action orbit. Player simplex constraints account for the multiplicity of each orbit inside each player's action set.

### Payoff-coordinate orbits

A payoff coordinate is `(player, joint_profile)`. A generator maps it to

```text
(player_perm[player], mapped_joint_profile)
```

Union--find over generator images computes payoff-coordinate orbits. The Reynolds projection assigns every coordinate the arithmetic mean over its orbit.

## 3. Sparse strategic-projection LP

The naive MPD formulation has a constraint for every pair of own actions. The implementation uses residual ranges instead.

For each slice `(player, opponent_profile)`, it introduces lower and upper residual variables. Every payoff coordinate contributes two inequalities:

```text
L <= original_payoff - surrogate_payoff <= U
```

and each slice contributes

```text
U - L <= t.
```

This reduces the strategic inequality count from quadratic to linear in the number of own actions per slice.

Optional structural equalities implement:

- `structure="zero_sum"`: `uhat_0(a) + uhat_1(a) = 0`;
- `structure="team"`: all players receive equal surrogate payoff at every profile.

SciPy's `linprog(method="highs")` solves the resulting sparse program.

## 4. Cycle solver

`cycle.py` independently solves the unrestricted projection.

### Graph construction

1. Compute payoff-coordinate orbit labels.
2. For every ordered unilateral comparison, create an edge between the two payoff-coordinate orbits.
3. Label the edge with the observed unilateral payoff difference.
4. When multiple upper-bound edges share endpoints, retain the smallest label because it is the strongest difference constraint.
5. Keep self-loops; they can be critical obstruction witnesses.

### Cycle mean

The projection defect is the largest mean of weights `-c_e`. Karp's dynamic program computes this value. The implementation reconstructs a critical cycle by predecessor tracing and validates its mean.

### Potential reconstruction

Shift every edge length by the computed defect. The shifted graph has no negative cycle. Bellman--Ford distances from an added source supply feasible potentials. These potentials are copied back to every payoff coordinate in the corresponding orbit to produce a nearest invariant game.

### Independent validation

The LP and cycle implementations share only basic orbit code. `tests/test_cycle.py` compares their objective values on deterministic examples and 100 randomized games. Agreement to numerical tolerance is an important regression check for edge orientation and cycle signs.

## 5. Zero-sum equilibrium LP

The ordinary row-player program maximizes a guaranteed value `v`:

```text
maximize v
subject to x^T A[:, j] >= v for every column j
           sum(x) = 1, x >= 0.
```

The column program is dual. The reported profile combines the two optimal strategies and is checked by explicit regret computation.

## 6. Invariant saddle-gap LP

The direct program minimizes

```text
alpha - beta
```

subject to

```text
A y <= alpha * 1
x^T A >= beta * 1^T
x and y lie in their simplices
x and y respect all action-orbit equalities.
```

The implementation parameterizes invariant strategies by one nonnegative variable per global action orbit. Separate weighted simplex equations enforce that row and column probabilities sum to one.

For an exactly invariant matrix, only one row best-response inequality and one column best-response inequality per orbit are retained. The `exact_invariant_game=True` flag is required before this compression is enabled; this prevents silently applying an invalid reduction to an approximate matrix.

## 7. Experiment families

### Nonstrategic separation

Start with an exactly lifted matrix game and add arbitrary functions of opponents' actions. The raw payoff projection error grows, while strategic distance remains zero.

### Certificate calibration

Add strategic Gaussian perturbations to a lifted zero-sum matrix. Compare:

- the structured strategic defect;
- actual saddle gap of the projected equilibrium;
- the certificate `2 * defect`;
- the best direct invariant saddle gap;
- Reynolds projection error.

### Compression hierarchy

Construct nested within-block permutation groups. Increasing group size reduces action-orbit variables but merges progressively more heterogeneous copies. The defect is monotone, while actual gap and direct invariant gap provide empirical operating points.

### Tightness

Use the cyclic `k`-action example. The measured ratio of invariant regret to defect equals `1 - 1/k`.

### Role assignment

Use a common-payoff complementary-role game with heterogeneous role preferences. This checks team-structure projection and illustrates that incentive certification does not itself ensure high welfare.

### Runtime scaling

Duplicate quotient actions without perturbation so the full and orbit programs solve exactly the same game. Warm both solvers, repeat each solve, and record medians.

### Sampling

Transform a planted matrix so payoff means lie in `[0,1]`, generate independent Bernoulli observations for every entry, project the estimated matrix, and compare the population regret with the distribution-free certificate.

## 8. Reproduction commands

From the repository root:

```bash
python -m pip install --no-build-isolation -e '.[dev]'
pytest
python experiments/run_all.py --seed 17 --replicates 10
```

Outputs:

```text
experiments/results/*.csv
experiments/results/summary.json
experiments/figures/*.pdf
experiments/figures/*.png
```

The committed summary for seed 17 and 10 replicates reports:

- maximum transfer violation below `3e-16` in magnitude;
- maximum Reynolds/optimal projection ratio `1.262946587456012`;
- sampling coverage `1.0` over 70 trials;
- largest runtime speedup `8.514622870684548`.

## 9. Numerical tolerances

Optimization tests use tolerances between `1e-9` and `1e-7`, depending on whether one or multiple LPs are composed. The randomized cycle/LP test uses a looser `5e-9` agreement threshold. These tolerances are for numerical validation only and do not appear in theorem statements.

## 10. Build and submission checks still required

Before final submission:

1. compile with the exact AAAI-27 distribution on a clean machine;
2. inspect the PDF for overfull boxes, figure legibility, embedded fonts, and seven-page main-content compliance;
3. run the full tests under the Python versions listed in the workflow;
4. regenerate every CSV and figure from a fresh checkout;
5. complete a line-by-line novelty comparison with exact-symmetry, near-potential-game, and abstraction literature;
6. replace provisional `and others` bibliography fields with complete author lists from archival metadata.
