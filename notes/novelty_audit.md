# Novelty and Claim-Boundary Audit

This note records the closest literature checked for **Almost Symmetric Games** and
the exact boundary of the manuscript's claims. It is intended to prevent both
overclaiming and accidental omission of a nearby result.

## 1. Exact finite-game symmetries

### Tewolde et al. (AAAI 2025)

**Computing Game Symmetries and Equilibria That Respect Them** studies exact
player/action relabelings in normal-form games, the complexity of discovering
automorphisms, and the complexity of finding equilibria that respect supplied
symmetries.

**Overlap**

- Same finite normal-form relabeling formalism.
- Same fixed strategy concept.
- Exact-symmetry equilibrium existence and zero-sum tractability are direct
  foundations for this paper.

**Difference**

- Their symmetry relation is exact; this paper quantifies distance to the fixed
  payoff subspace.
- This paper uses deviation-incentive distance rather than literal payoff
  mismatch.
- The sparse projection LP, maximum-mean-cycle obstruction certificate,
  additive transfer theorem, and sharp Reynolds approximation analysis are not
  supplied by the exact-symmetry framework.
- This paper assumes the candidate group is supplied and does not claim to
  improve exact automorphism discovery.

### Ghosh and Hollender (ACM TEAC 2026)

**The Complexity of Symmetric Bimatrix Games with Common Payoffs** proves
CLS-completeness of computing symmetric equilibria in a restricted exact class.

**Relevance**

This result reinforces an important scope statement: projection onto a symmetric
common-payoff game is tractable, but computing a symmetry-respecting Nash
equilibrium in a general-sum/team surrogate need not be. The present paper's
strongest end-to-end algorithmic theorem is therefore deliberately zero-sum.

## 2. Strategic distances between games

### Candogan, Ozdaglar, and Parrilo (GEB 2013)

**Near-Potential Games: Geometry and Dynamics** introduces maximum pairwise
difference (MPD) to compare unilateral deviation incentives and studies distance
to the potential-game subspace.

**Overlap**

- The seminorm used here is MPD.
- Its kernel consists of opponent-action-dependent, strategically irrelevant
  payoff components.
- The mixed-strategy incentive perturbation argument is a standard consequence
  of MPD.

**Difference**

- The target set here is the fixed subspace of an arbitrary player/action
  relabeling group, not the potential-game subspace.
- The orbit-graph reduction yields a new maximum-mean-cycle formula specific to
  symmetry identifications.
- The paper does not claim to introduce MPD itself.

### Marris, Gemp, and Piliouras (2023)

**Equilibrium-Invariant Embedding, Metric Space, and Fundamental Set of
2x2 Normal-Form Games** develops equilibrium- and better-response-invariant
metrics and geometric embeddings, with detailed classification of 2x2 games.

**Difference**

- Their objective is geometric representation/classification.
- The present work handles arbitrary finite games and candidate relabeling
  groups and optimizes distance to a group-fixed subspace.
- The equilibrium transfer, critical-cycle witness, and orbit-compressed
  algorithms are distinct.

## 3. Approximate and partial symmetry in MARL

### Yu et al. (AAAI 2024)

**Leveraging Partial Symmetry for Multi-Agent Reinforcement Learning** defines
partially symmetric Markov games, bounds performance degradation from symmetry
exploitation, and learns how strongly to apply a symmetry prior.

### Yardim and He (L4DC 2025)

**Exploiting Approximate Symmetry for Efficient Multi-Agent Reinforcement
Learning** studies approximate permutation invariance in finite-player dynamic
games, induced mean-field models, approximate Nash policies, and sample
complexity.

**Overlap**

- All three works motivate symmetry under heterogeneity.
- All provide approximation guarantees after imposing or exploiting symmetry.

**Difference**

- The MARL papers concern dynamic games, policy learning, and model/sample
  complexity.
- This paper concerns an explicitly represented finite normal-form game and an
  arbitrary supplied player/action relabeling group.
- Its main object is the *minimum unilateral-incentive perturbation* that makes
  the group exact.
- Its critical-cycle certificate and exact projection algorithms do not follow
  from dynamic-game approximate-symmetry bounds.

**Claim boundary**

The manuscript must not say that approximate symmetry in games or MARL is
unexplored. It may claim a new incentive-preserving projection and certificate
framework for finite normal-form player/action symmetries.

## 4. Zero-shot coordination and symmetry-based conventions

### Hu et al. (ICML 2020)

**Other-Play for Zero-Shot Coordination** uses known exact symmetries to avoid
arbitrary conventions.

**Difference**

Other-Play optimizes policies robust to relabelings. The present work audits how
far a supplied relabeling is from exact and certifies equilibrium regret after
enforcing it. It does not claim a new zero-shot coordination algorithm.

## 5. Abstraction and aggregation

### Ravindran and Barto (2004); Kroer and Sandholm (EC 2014)

Approximate homomorphisms and extensive-form game abstraction provide solution
quality bounds under aggregation.

**Difference**

- Those abstractions merge states/actions/information sets in sequential
  decision processes or game trees.
- This paper identifies payoff coordinates through a normal-form relabeling
  group and measures error directly in unilateral incentives.
- No claim is made yet for stochastic or extensive-form games.

## 6. Classical graph optimization

The maximum-mean-cycle value algorithm is classical (Karp, 1978), as are
difference constraints and shortest-path feasibility.

**Novel component**

The contribution is the reduction of strategic symmetry projection to this graph:
payoff-coordinate orbits are vertices, unilateral comparisons are labeled edges,
and the optimal symmetry defect is the critical cycle mean. The implementation
uses Karp for the value, tight reduced edges for a certified cycle, and
difference-constraint potentials for the surrogate.

The manuscript must not describe Karp's algorithm itself as new.

## 7. Claims supported by the current theorem stack

The current draft can defensibly claim:

1. A strategic symmetry defect for arbitrary finite player/action relabeling
   groups based on MPD.
2. An exact sparse LP for the nearest invariant surrogate.
3. An exact maximum-mean-cycle characterization of the unrestricted projection.
4. A local critical-cycle lower-bound certificate and constructive surrogate.
5. Additive `epsilon + delta` equilibrium transfer.
6. Existence of a group-respecting `delta_G`-Nash equilibrium.
7. Asymptotic tightness of the coefficient one.
8. A closed-form Reynolds projection with approximation factor two.
9. An explicit family attaining ratio `2 - 2/d^2`, proving factor-two
   asymptotic tightness.
10. Structured zero-sum projection and direct invariant saddle-gap LPs.
11. Finite-sample certificates under entrywise independent bounded sampling.
12. Orbit compression and all theorem diagnostics on explicit laptop-scale games.

## 8. Claims intentionally excluded

The paper does **not** claim:

- the first study of approximate symmetry in games;
- a new game-distance seminorm independent of MPD;
- automatic discovery of an optimal approximate symmetry group;
- tractable general-sum Nash equilibrium computation;
- welfare preservation from small strategic defect;
- compact complexity for graphical, polymatrix, stochastic, or extensive-form
  representations;
- tight finite-sample rates under partial or trajectory-dependent coverage;
- large-scale MARL performance.

## 9. Remaining search terms before final upload

A final author-side search should include combinations of:

- approximate game automorphism;
- approximate normal-form game symmetry;
- distance to symmetric games;
- payoff tensor symmetry projection;
- deviation graph cycle consistency;
- Chebyshev potential fitting on directed graphs;
- group-invariant Nash approximation;
- robust symmetric equilibrium;
- approximate equivariance game theory;
- quotient games unilateral incentive distance.

Any newly found result should be compared against the graph reduction, sharp
constants, and supplied-group setting—not only against the phrase “approximate
symmetry.”
