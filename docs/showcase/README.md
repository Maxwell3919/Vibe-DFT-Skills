# README showcase assets

The root README figures are deterministic visual demonstrations produced by
the repository's own `cif-structure-analysis` and `dft-postprocess` code. They
are synthetic fixtures, not calculation results or reference structures.

Regenerate the committed PNG files from the repository root:

```bash
python3 docs/showcase/generate_showcase.py
```

The generator creates a synthetic P1 layered CIF in a temporary directory,
runs the CIF analyzer (including the Mo-S nearest-bond target matcher), and
copies the three static projections to `docs/images/`. It also creates
synthetic normalized band/DOS tables in the temporary directory and invokes
the postprocessing `bands-dos` command. Temporary tables and reports are not
committed; only the generator and the four final PNG files are versioned.
