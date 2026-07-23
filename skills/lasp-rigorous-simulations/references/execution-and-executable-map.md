# LASP 3.7.3 execution and executable map

## Public evidence and native-validation state

The LASP authors' 2024 review identifies LASP 3.7 and its high-level
capabilities. On 2026-07-22 the official LASP Hub public download page identified
the distributed CPU package more specifically as LASP `3.7.3-ac` and
`3.7.3-pro`, for Linux with Intel MPI and Intel Compiler 2017 or newer. It also
displayed the direct and four-rank MPI commands below.

The page advertises a LASP manual and examples, but retrieving them requires an
authorized LASP Hub session. No authorized version-matched manual, example
archive, binary, or license terms were available to this repository review.
Therefore the executable entry is documented, while input/output/restart
semantics remain unsupported. No native LASP run was performed; the maintainer
machine was macOS arm64 and had no `lasp`, Intel MPI, or Intel compiler in
`PATH`.

## Official executable entry

The public quick-install panel gives these exact shapes:

```text
[LASP Installation DIR]/Src/lasp
mpirun -np 4 [LASP Installation DIR]/Src/lasp
```

It also says that an Expert package is unpacked, built in `Src`, and tried with
an official example. This establishes the executable basename and launcher
shape only. It does not establish that arbitrary rank counts, CLI arguments,
fixed filenames, scheduler launchers, or environment variables are supported.
Use the exact authorized package README/manual and site MPI policy before a
real launch.

Do not invent `lasp --version`, `lasp -h`, an input-file flag, or stdin
redirection. No such probe was verified in the public page. If an authorized
manual does not provide a side-effect-free version option, bind version to the
download/build manifest, archive and executable hashes, edition/license record,
and version evidence from an authorized normal example run.

## Non-executing inventory probes

After lawful installation, inventory without launching LASP:

```text
command -v lasp
command -v mpirun
mpirun --version
file "$(command -v lasp)"
sha256sum "$(command -v lasp)"
```

The last command assumes GNU/Linux, the platform named by the public page.
Record the exact Intel MPI and Intel compiler/runtime releases supplied or
required by the authorized distribution. Do not treat the string “2017 or
above” as proof that every newer oneAPI release is binary compatible. Do not
apply LASP GPUNN 4.0-beta, CUDA, or `laspai.com` requirements to the CPU 3.7.3
package: the public page treats GPUNN as a separate product and says it is no
longer released or maintained on LASP Hub.

## Execution preconditions

A future executor may use the official command shape only after all of these
are true:

1. the user has lawful access to the exact academic or professional package;
2. edition, expiry/use rights, archive hash, executable hash, platform,
   compiler/runtime, MPI implementation, and any interface licenses are bound;
3. the authorized matching manual/README and official example are retained and
   independently reviewed;
4. exact input/model closure, working directory, output names, units, restart
   state, failure markers, and resource needs are known from those materials;
5. execution authority names the host, command, ranks, resources, time window,
   clean output root, and stop policy.

The academic edition is described publicly as academic testing software that
expires after one month. The professional edition is described as having no
expiry limit and access/support benefits. These page statements are not a
complete software license; exact authorized terms still control.

## Fail-closed command template

Do not turn this section into an executable script. Once the preconditions are
met, the documented outer shape is:

```text
cd <authorized-official-example-or-reviewed-case-directory>
mpirun -np <AUTHORIZED_RANK_COUNT> <absolute-authorized-path>/Src/lasp \
  > lasp.stdout 2> lasp.stderr
```

`<AUTHORIZED_RANK_COUNT>` is not inferred from the public example's `4`.
Before implementation, confirm through the retained manual whether LASP reads
fixed files, accepts arguments, writes additional streams, or requires a
specific launcher. Until then, this template is documentary and
`execution_authorized=false`.

## Input, output, units, failure, and restart boundary

The public download page does not provide a complete input grammar, keyword
defaults, units map, output grammar, normal-completion marker, fatal marker
catalog, restart file list, or exact continuation semantics. The author paper's
capability statements and older paper mentions of `lasp.in` are insufficient
to implement 3.7.3 parsing.

Consequently:

- keep units, ensemble, boundaries, time step, seed, observables, and output
  cadence as project intentions, not LASP facts;
- hash and label user-supplied inputs/models as opaque artifacts;
- treat every output as opaque until a version-matched extractor exists;
- require process/scheduler exit state plus documented normal/fatal markers
  before technical completion, once those markers are authorized;
- represent any proposed restart as `opaque-state-continuation`, bind parent
  run/state hashes, and set `exact_continuation_claim=false`;
- do not infer state coverage from a familiar filename or another engine.

Any nonzero exit, signal, timeout, MPI abort, license/expiry refusal,
non-finite/corrupt output, missing authoritative completion evidence, or
input/output contradiction blocks acceptance. A zero exit alone is not a
completion, convergence, or scientific-validity claim.

## Typical acceptance workflow

1. Run the documentary `plan` and record the exact evidence gaps.
2. Obtain the authorized 3.7.3 distribution, complete manual, example set, and
   terms through LASP Hub; keep restricted contents outside this repository.
3. Independently implement and adversarially test version-matched syntax,
   output, unit, failure, and restart parsers with lawful fixtures.
4. Capture the exact binary/environment/license record and authorize one
   bounded official example run.
5. Compare expected and observed artifacts, then validate task-specific
   numerical, statistical, model-domain, and scientific gates.
6. Promote the Skill only through explicit lifecycle review. Until then, use
   the current guard only for opaque inventory and no-positive-claim routing.

## Official URLs

- LASP Hub download route: <http://www.lasphub.com/#/lasp/download>
- LASP Hub: <http://www.lasphub.com/>
- Author review and data-availability statement:
  <https://doi.org/10.1021/prechem.4c00060>
- Open article copy: <https://pmc.ncbi.nlm.nih.gov/articles/PMC11672538/>
