# Environment, license, and execution boundary

## Offline audit environment

- Python 3.10 or newer; standard library only.
- Read-only candidate source and calculation evidence.
- No GPUMD executable, GPU driver, compiler, scheduler, network, or credentials are needed.

## Future execution environment

Read [execution-and-executable-map.md](execution-and-executable-map.md). Before a separate authorized execution layer runs GPUMD, record the exact executable hash, v5.3 banner, source commit, compiler/build options, CUDA or ROCm/HIP stack, GPU model and capability, driver/runtime compatibility, precision-affecting settings, resource limits, working directory, immutable input hashes, and clean output policy. Official current installation material describes NVIDIA CUDA and AMD ROCm/HIP paths and does not provide an Apple Silicon execution route.

The reviewed v5.3 program has no documented side-effect-free `--version` command. Use source/build provenance plus the normal-run banner; never launch it merely to probe a version. The real official launch is the no-argument `path/to/gpumd` from a directory containing fixed-name inputs. Capture stdout and stderr separately and bind the process/scheduler exit state.

Execution must be explicitly authorized for the named host, software, command class, resource envelope, output tree, and time window. This candidate grants none of that authority.

## Legal boundary

Exact v5.3 source headers state GNU GPL version 3 or later. The repository README abbreviates this as GPL version 3. Preserve the more specific source-header result as `GPL-3.0-or-later` and reconcile the planned registry's `GPL-3.0-only` entry before activation.

Potential files, NEP models, datasets, reference structures, and output data have independent rights. Require a source URL or internal authority record and explicit license status for each. Do not redistribute proprietary or unknown-license model contents in fixtures.

## Privacy boundary

Use anonymous IDs and basenames. Do not place usernames, hostnames, scheduler IDs, private paths, unpublished structures, raw restricted potentials, tokens, or credentials in plans, reports, examples, or logs.
