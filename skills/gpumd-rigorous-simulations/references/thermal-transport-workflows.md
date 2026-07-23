# GPUMD v5.3 thermal-transport workflows

Use this reference to plan Green–Kubo equilibrium MD (EMD) or homogeneous
nonequilibrium MD (HNEMD). These routes are design-only in the current guard.
Do not present their commands as parser-validated or execution-authorized.

## Contents

- [Common evidence contract](#common-evidence-contract)
- [Green-Kubo EMD](#green-kubo-emd)
- [HNEMD](#hnemd)
- [Two-dimensional and fluid limits](#two-dimensional-and-fluid-limits)
- [Convergence and uncertainty](#convergence-and-uncertainty)
- [Failure routing](#failure-routing)

## Common evidence contract

Before choosing a transport method, establish:

- the tensor component(s), temperature, pressure/volume convention, material
  state, and classical/quantum interpretation of the claim;
- potential validity for forces, virials, heat current, and the sampled phase;
- cell dimensions, boundary conditions, finite-size plan, and direction labels;
- integration time-step evidence and a separately equilibrated starting state;
- estimator, correlation/averaging window, replica plan, uncertainty method,
  and acceptance bounds fixed before production;
- exact v5.3 command/output grammar, executable/build/GPU identity, and clean
  segment outputs.

Technical completion, a smooth running-conductivity curve, and an apparently
flat interval are not independent-replica uncertainty or model validation.

## Green-Kubo EMD

Official v5.3 syntax:

```text
compute_hac <sampling_interval> <correlation_steps> <output_interval>
```

The command samples heat current at the first interval, correlates up to the
second number of sampled steps, averages output by the third interval, and
writes `hac.out`. It is non-propagating because analysis commands belong to one
`run` block.

The v5.3 manual example uses `time_step 1`, samples every 10 integration steps,
uses 100000 correlation steps, and runs 10000000 integration steps. The manual
calls a maximum correlation length equal to one tenth of the available heat
current samples a sound choice in that example. Treat that ratio as an example,
not a universal default.

`hac.out` contains correlation time in ps, five decomposed heat-current
autocorrelation columns, and five running-conductivity columns in W/mK. For
ordinary 3D interpretation, the documented in-plane and out-of-plane
contributions can be summed for the corresponding total x/y component.

Operational workflow:

1. equilibrate without collecting production HAC evidence;
2. start independent production segments from declared decorrelated states;
3. verify stationary thermodynamic behavior without selecting a favorable
   interval after viewing conductivity;
4. examine decay/noise of the HAC and stability of the integrated result over
   a predeclared correlation-time window;
5. aggregate independent runs with a stated estimator and uncertainty;
6. repeat cell-size, duration, time-step, and potential-domain checks needed by
   the claim.

Do not average correlated windows as though they were independent replicas.
Block length must exceed relevant correlation times, and the effective sample
size—not merely the number of saved rows—controls uncertainty.

## HNEMD

Official v5.3 syntax:

```text
compute_hnemd <output_interval> <Fe_x> <Fe_y> <Fe_z>
```

The driving field components use Å⁻¹. Normally only one component is nonzero.
The selected direction determines which conductivity-tensor column is driven;
retain the documented axis order rather than relabeling components by habit.
Results are running averages in `kappa.out` with five columns in W/mK, including
the documented in-plane/out-of-plane decomposition.

Official v5.3 method constraints:

- keep the field small enough for linear response;
- control temperature because the driving field heats the system;
- use a global thermostat; the manual recommends Nose–Hoover chain;
- do not use Langevin for HNEMD because it changes the relevant dynamics.

Operational workflow:

1. equilibrate at the target state without the driving field;
2. apply one declared field direction in a clean production segment;
3. run multiple independent initial states;
4. repeat at two or more smaller field magnitudes and require conductivity to
   agree within the predeclared uncertainty (linear-response check);
5. check temperature control and absence of systematic drift/heating;
6. obtain other tensor columns from separate direction-specific runs;
7. assess running-average convergence, replicas, size, duration, and model
   sensitivity.

Never choose the strongest field solely because it converges visually faster.
A field-dependent result is evidence that the linear-response claim is not yet
established.

## Two-dimensional and fluid limits

The v5.3 output decomposes x/y heat current into in-plane and out-of-plane
vibrational contributions, which is useful for 2D/layered systems. That
decomposition does not resolve the geometric normalization convention for a
2D material. State the cell volume or effective thickness convention and make
comparisons using the same convention; do not bury vacuum dependence inside a
reported W/mK value.

The built-in `compute_hac` and HNEMD outputs include only the potential part of
the heat current. The manual explicitly warns that convective heat current can
matter for fluids. For Green–Kubo, it directs users to output potential and
kinetic heat-current data with `compute` and postprocess separately; for HNEMD,
the v5.3 output documentation says source modification is required when the
convective contribution is important. Stop rather than reuse a lattice-only
estimator for a fluid claim.

## Convergence and uncertainty

Predeclare and report at least:

| Gate | Green–Kubo evidence | HNEMD evidence |
|---|---|---|
| state | equilibrated, stationary production | equilibrated state plus controlled driven temperature |
| estimator | HAC sampling and integration window | running average and field direction/magnitude |
| independence | replicas or defensible effective samples | independent starting states/replicas |
| method-specific | correlation decay and window stability | linear-response field sweep |
| geometry | cell-size and volume/thickness convention | cell-size and volume/thickness convention |
| model | force/virial/heat-current domain validation | force/virial/heat-current domain validation |
| uncertainty | replica/block estimator with declared interval | replica/block estimator with declared interval |

Operational heuristic: convergence should be demonstrated over a range of
admissible analysis windows and repeated states, not by selecting one plateau.
If the final uncertainty is comparable to the claimed trend, weaken or withhold
the trend.

## Failure routing

- Noisy/nondecaying HAC: extend statistically independent sampling, revisit
  correlation window, state stationarity, size, and model; do not smooth away
  the tail without a declared estimator.
- Drifting Green–Kubo integral: inspect correlation convergence, energy drift,
  equilibration, finite size, and replica dispersion.
- HNEMD heating: check thermostat choice/coupling, field magnitude, time step,
  and model stability.
- HNEMD field dependence: reduce the field and extend sampling; linear response
  is not established.
- Direction/tensor mismatch: retain one-field-per-run provenance and the exact
  v5.3 column map.
- Implausibly small error bars: inspect time correlation, shared ancestry, and
  whether blocks were incorrectly counted as independent.
- 2D vacuum dependence or fluid convection: correct the estimator/normalization
  contract before interpreting conductivity.

Primary v5.3 sources: [`compute_hac`](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/gpumd/input_parameters/compute_hac.rst),
[`hac.out`](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/gpumd/output_files/hac_out.rst),
[`compute_hnemd`](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/gpumd/input_parameters/compute_hnemd.rst),
[`kappa.out`](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/gpumd/output_files/kappa_out.rst),
and [heat-transport theory](https://github.com/brucefan1983/GPUMD/blob/f2b46c5d528e985a5bf68becd442b18c0e04396c/doc/theory/heat_transport.rst).
