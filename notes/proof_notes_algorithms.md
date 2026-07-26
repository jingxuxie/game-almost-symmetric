# Algorithm and Reproducibility Notes

This document records the implementation behind **Almost Symmetric Games** and
maps every numerical output to a theorem claim. It is intentionally more
explicit than the main paper so that the projection, certificate, and orbit
reductions can be independently audited.

## 1. Data model

`NormalFormGame.payoffs` has shape

```text
(n_players, action_count_player_0, ..., action_count_player_{n-1})
```

A `Relabeling` stores:

- `player_perm[i]`: destination of source player `i`;
- `action_perms[i][a]`: destination action of source action `a`.

Every action map is checked to be a bijection onto the destination player's
action set. A candidate finite group is supplied through generators; the core
algorithms do not enumerate every group element.

## 2. Orbit construction

Two orbit systems are used.

### Action orbits

The disjoint union of player-action pairs is indexed with player offsets.
Generator images are joined with union--find. A symmetry-respecting mixed
profile assigns equal probability to coordinates in the same global orbit.
Separate player-simplex equations weight an orbit variable by the number of its
coordinates owned by that player. This remains valid when a generator exchanges
players.

### Payoff-coordinate orbits

A payoff coordinate is `(player, joint_profile)`. A generator maps it to

```text
(player_perm[player], mapped_joint_profile)
```

Union--find over generator images computes the fixed-subspace coordinates. The
Reynolds projection assigns every coordinate the arithmetic mean of its orbit.

## 3. Strategic distance

For games `Gamma` and `H`, the residual in a player/opponent-profile slice is

```text
r_i(a_i, a_-i) = u_i(a_i, a_-i) - h_i(a_i, a_-i).
```

The strategic distance is the maximum residual range over all slices:

```text
max_{i,a_-i} max_{a_i} r_i - min_{a_i} r_i.
```

This is exactly maximum pairwise difference (MPD). Opponent-action-dependent
payoff shifts are in its kernel, so they do not affect projections or
certificates.

## 4. Sparse strategic-projection LP

The naive MPD formulation has one inequality for every pair of own actions. The
implementation instead introduces lower and upper residual variables for each
slice:

```text
L <= original_payoff - surrogate_payoff <= U
U - L <= t.
```

Every payoff entry contributes two inequalities and every slice contributes one
width inequality. Generator equalities constrain the surrogate to the exact
fixed subspace. Optional structure equalities implement:

- `structure="zero_sum"`: `uhat_0(a) + uhat_1(a) = 0`;
- `structure="team"`: all players receive the same surrogate payoff at a
  profile.

SciPy's HiGHS interface solves the resulting sparse LP. The unrestricted and
structured defects are deliberately distinct quantities.

## 5. Maximum-mean-cycle solver

`cycle.py` independently solves the **unrestricted** strategic projection.

### Graph construction

1. Compute payoff-coordinate orbit labels.
2. For every ordered unilateral comparison, create a directed edge from the
   baseline-action orbit to the deviation-action orbit.
3. Label the edge with the observed unilateral payoff difference.
4. Keep the smallest label among parallel upper-bound edges with the same
   endpoints.
5. Retain self-loops; a symmetry identification can make one comparison an
   immediate obstruction.
6. Include every ordered comparison, so the reverse inequality needed for the
   absolute error is also present.

### Value computation

For an edge label `c_e`, use weight `w_e = -c_e`. The projection defect is the
maximum directed-cycle mean of these weights. Karp's dynamic program computes
the value `lambda` in polynomial time.

### Certified witness extraction

Karp's value table is not used as a heuristic cycle backtracker. Instead:

1. form reduced weights `w'_e = w_e - lambda`;
2. compute max-plus path potentials `h`, for which
   `h(head) >= h(tail) + w'_e`;
3. retain edges whose inequality is tight to numerical tolerance;
4. find a directed cycle in this tight-edge subgraph;
5. verify that consecutive edges close and that the cycle mean equals
   `lambda`.

The reduced graph has no positive cycle and at least one zero-weight critical
cycle. Nonnegative edge slacks telescope to zero on such a cycle, so every
critical-cycle edge is tight. This makes the returned witness a checkable lower
bound certificate, not merely a diagnostic path.

### Surrogate reconstruction

At defect `lambda`, the one-sided lengths `c_e + lambda` contain no negative
cycle. Bellman--Ford-style difference-constraint relaxation recovers feasible
orbit potentials. Copying those potentials to all payoff coordinates in the
orbit produces a nearest invariant surrogate, whose strategic distance is
checked directly.

### Regression coverage

The tests independently verify:

- a critical self-loop;
- compressed parallel edges;
- global action orbits under a player swap;
- witness closure and mean;
- reconstructed-surrogate distance;
- equality with the projection LP on 100 generated games.

## 6. Sharpness constructions

### Equilibrium-transfer constant

A player has `k` cyclically identified actions, one of value one and the rest of
value zero. The defect is one and the unique invariant strategy has regret
`1 - 1/k`. This proves the additive coefficient one is asymptotically tight.

### Reynolds factor two

`experiments/sharpness.py` implements the two-block family from the supplement.
For block size `d`, the exact quantities are

```text
optimal defect       = 1
Reynolds distance    = 2 - 2 / d**2
approximation ratio  = 2 - 2 / d**2.
```

The LP, cycle solver, and direct distance calculation are run independently.
The experiment compares their outputs with the closed-form formula.

## 7. Zero-sum equilibrium programs

### Ordinary equilibrium

The row-player LP maximizes a guaranteed value and the column-player LP is its
dual. The returned profile is evaluated by explicit row and column regret.

### Invariant saddle-gap LP

The direct program minimizes

```text
alpha - beta
```

subject to

```text
A y <= alpha * 1
x^T A >= beta * 1^T
x and y are probability distributions
x and y respect all global action-orbit equalities.
```

For fixed strategies, the optimal `alpha` and `beta` make the objective exactly
the saddle gap.

For a matrix known to be exactly invariant, row best-response values are
constant over row-action orbits and column best-response values over
column-action orbits. The implementation then retains one representative
constraint per orbit. Constraint compression is disabled unless the caller
sets `exact_invariant_game=True`.

## 8. Experiment families

### Nonstrategic separation

Start with an exactly lifted matrix game and add arbitrary functions of the
opponent's action. Raw payoff projection error grows while strategic defect
stays zero.

### Certificate calibration

Add strategic Gaussian perturbations to a lifted zero-sum game. Compare the
structured defect, transferred saddle gap, certificate, direct invariant gap,
and Reynolds distance.

### Compression hierarchy

Increase the size of within-block action groups. Larger groups produce fewer
strategy variables but a larger defect. This is the empirical
compression--fidelity frontier.

### Role assignment

Use a common-payoff complementary-role game with heterogeneous player-role
preferences. The study reports strategic defect, invariant-profile regret, and
welfare loss to demonstrate that incentive certification is not a welfare
theorem.

### Runtime scaling

Duplicate quotient actions without perturbing the game. The full and quotient
programs solve the same strategic problem, while only the full dimension grows.

### Sampling

Treat every row-player payoff as a Bernoulli mean and set the column payoff to
its negative. Project the empirical zero-sum game and compare population regret
with the entrywise-Hoeffding certificate.

## 9. Reproduction commands

From the repository root:

```bash
python -m pip install -e ".[dev]"
pytest
PYTHONPATH=src python -m experiments.run_all \
  --seed 17 \
  --replicates 20 \
  --sampling-replicates 40
make -C paper
python scripts/check_submission.py
```

Or run the complete pipeline with

```bash
make -C paper check
```

A smaller deterministic CI sweep is available through

```bash
PYTHONPATH=src python -m experiments.run_all --quick
```

## 10. Submission validation

GitHub Actions runs tests on Python 3.10 and 3.12, regenerates a smoke experiment
suite, compiles the main paper and supplement, and checks:

- technical content through at most page seven;
- US-letter page size;
- anonymous PDF author metadata;
- embedded fonts and absence of Type 3 fonts;
- unresolved references or citations;
- material overfull boxes.

The generated PDFs, summary JSON, sharpness CSV, and sharpness figure are
uploaded as workflow artifacts.

## 11. Numerical tolerances

Optimization checks use tolerances between `1e-9` and `1e-7`, depending on how
many LPs are composed. Witness extraction begins with a scale-aware `1e-12`
tightness tolerance and increases it only to absorb floating-point error; the
returned cycle is always revalidated against the Karp value. Tolerances support
regression testing and do not alter theorem statements.

## 12. Scope boundaries

- The candidate group is supplied.
- The cycle formula is for the unrestricted fixed subspace; structured classes
  use the LP.
- Polynomial time is measured in the explicit normal-form table size.
- General-sum equilibrium computation remains hard.
- Strategic defect certifies unilateral incentives, not welfare.
