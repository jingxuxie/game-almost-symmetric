# Algorithm and Reproducibility Notes

This document records the implementation behind **Almost Symmetric Games** and
maps every numerical output to a theorem claim.

## 1. Data model

`NormalFormGame.payoffs` has shape

```text
(n_players, action_count_player_0, ..., action_count_player_{n-1})
```

A `Relabeling` stores a player permutation and one source-to-destination action
bijection per player. Every map is validated against the destination action
set. Candidate finite groups are supplied through generators; the core
algorithms do not enumerate all group elements.

## 2. Orbit construction

### Action orbits

Union--find acts on the disjoint union of player-action pairs. A
symmetry-respecting profile assigns equal probability to coordinates in the
same global orbit. Separate player-simplex equations weight each orbit variable
by the number of coordinates that the orbit contributes to that player. This
also handles generators that exchange players.

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

The strategic distance is the maximum residual range over all slices. It is
maximum pairwise difference (MPD). Opponent-action-dependent shifts lie in its
kernel and therefore do not affect projections or equilibrium certificates.

## 4. Sparse strategic-projection LP

The implementation introduces lower and upper residual variables for each
slice:

```text
L <= original_payoff - surrogate_payoff <= U
U - L <= t.
```

Every payoff entry contributes two inequalities and every slice contributes one
width inequality. Generator equalities constrain the surrogate to the exact
fixed subspace. Optional structure equalities implement zero-sum and
common-payoff projections. SciPy's HiGHS interface solves the sparse LP.

## 5. Maximum-mean-cycle solver

`cycle.py` independently solves the **unrestricted** strategic projection.

### Graph construction

1. Compute payoff-coordinate orbit labels.
2. For every ordered comparison between distinct own actions, create an edge
   from the baseline-action orbit to the deviation-action orbit.
3. Label the edge with the observed unilateral payoff difference.
4. Keep the smallest label among parallel upper-bound edges with identical
   endpoints.
5. Retain self-loops.
6. Include every reverse comparison.

If every player has one action, the graph is empty and the defect is defined as
zero.

### Value computation

For edge label `c_e`, use weight `w_e=-c_e`. The projection defect is the
maximum directed-cycle mean of these weights. Karp's dynamic program computes
the value `lambda` in polynomial time.

### Certified witness extraction

Karp's value table is not used as a heuristic cycle backtracker. Instead:

1. form reduced weights `w'_e=w_e-lambda`;
2. compute max-plus path potentials `h` with
   `h(head)>=h(tail)+w'_e`;
3. retain numerically tight edges;
4. find a directed cycle in the tight-edge graph;
5. verify closure and equality of its mean with `lambda`.

The reduced graph has no positive cycle and every nonempty graph has a
zero-weight critical cycle. Nonnegative slacks telescope to zero on a critical
cycle, so every critical edge is tight.

### Surrogate reconstruction

At defect `lambda`, lengths `c_e+lambda` contain no negative cycle.
Bellman--Ford-style difference-constraint relaxation recovers orbit potentials.
The reconstructed surrogate's strategic distance is checked directly.

### Regression coverage

The tests verify:

- an empty incentive graph;
- a critical self-loop;
- compressed parallel edges;
- global action orbits under a player swap;
- witness closure and mean;
- reconstructed-surrogate distance;
- equality with the projection LP on 100 generated games.

## 6. Sharpness constructions

### Equilibrium-transfer coefficient

A player has `k` cyclically identified actions, one of value one and the rest of
value zero. The defect is one and the invariant strategy has regret `1-1/k`.

### Reynolds factor two in zero-sum games

`experiments/sharpness.py` implements a zero-sum construction. The row player
has one orbit of `d` actions. The column player has two `d`-action blocks. A
distinguished row receives payoffs `(0,1)` across the two blocks; all other rows
receive `(1,0)`. The column payoff is the negative row payoff.

The exact quantities are

```text
unrestricted defect       = 1
zero-sum structured defect = 1
Reynolds distance          = 2 - 2 / d
approximation ratio        = 2 - 2 / d.
```

The structured LP, unrestricted cycle solver, and direct distance calculation
are run independently and compared with the closed form.

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
x and y respect global action-orbit equalities.
```

For fixed strategies, the objective is exactly the saddle gap. For a matrix
known to be exactly invariant, one representative best-response constraint per
relevant action orbit is sufficient. Constraint compression is disabled unless
`exact_invariant_game=True`.

## 8. Experiment families

### Nonstrategic separation

Start with an exactly lifted game and add arbitrary functions of the opponent's
action. Raw payoff projection error grows while strategic defect stays zero.

### Certificate calibration

Add strategic perturbations to a lifted zero-sum game. Compare the structured
defect, transferred saddle gap, certificate, direct invariant gap, and Reynolds
distance.

### Compression hierarchy

Increase the size of within-block groups. Larger groups produce fewer variables
but a larger defect.

### Role assignment

Use a common-payoff complementary-role game with heterogeneous player-role
preferences. Report defect, invariant-profile regret, and welfare loss to show
that incentive certification is not a welfare theorem.

### Runtime scaling

Duplicate quotient actions without perturbing the game. Full and quotient
programs solve the same strategic problem while only the full dimension grows.

### Sampling

Treat every row-player payoff as a Bernoulli mean and set the column payoff to
its negative. Compare population regret with the entrywise-Hoeffding
certificate.

## 9. Reproduction commands

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
pytest
PYTHONPATH=src python -m experiments.run_all \
  --seed 17 \
  --replicates 20 \
  --sampling-replicates 40
make -C paper
python scripts/check_submission.py
```

The complete pipeline is

```bash
make -C paper check
```

and a smaller CI sweep is

```bash
PYTHONPATH=src python -m experiments.run_all --quick
```

## 10. Submission validation

GitHub Actions runs tests on Python 3.10 and 3.12, regenerates a smoke experiment
suite, compiles the main paper and supplement, and checks:

- technical content through at most page seven;
- US-letter page size;
- anonymous PDF metadata;
- embedded fonts and absence of Type 3 fonts;
- unresolved references or citations;
- material overfull boxes.

The generated PDFs, summary JSON, sharpness CSV, and sharpness figure are
uploaded as workflow artifacts.

## 11. Numerical tolerances

Optimization checks use tolerances between `1e-9` and `1e-7`. Witness
extraction begins with a scale-aware `1e-12` tightness tolerance and increases
it only for floating-point error; the returned cycle is always revalidated
against the Karp value.

## 12. Scope boundaries

- The candidate group is supplied.
- The cycle formula is for the unrestricted fixed subspace; structured classes
  use the LP.
- Polynomial time is measured in the explicit normal-form table size.
- General-sum equilibrium computation remains hard.
- Strategic defect certifies incentives, not welfare.
