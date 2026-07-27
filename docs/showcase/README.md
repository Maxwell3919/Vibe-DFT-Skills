# README showcase assets

The root README figures are deterministic visual demonstrations produced from
repository registries, the `cif-structure-analysis` analyzer, the
`dft-postprocess` plotting route, and synthetic tables embedded in the
generator. They are not calculation results, reference structures, or
recommended convergence thresholds.

Regenerate the committed PNG files from the repository root:

```bash
python3 docs/showcase/generate_showcase.py
```

The generator creates a synthetic P1 layered CIF in a temporary directory,
runs the CIF analyzer (including the Mo-S nearest-bond target matcher), and
copies the three static projections to `docs/images/`. It also:

- creates normalized synthetic band/DOS tables and invokes the repository
  `bands-dos` command;
- renders separate representation, sampling, energy, and force convergence
  traces;
- renders one compact structure-to-observable evidence figure;
- derives the scientific-software landscape directly from
  `registry/software-registry.yaml`.

Temporary tables and reports are not committed. Seven final PNG files are
versioned:

```text
docs/images/cif-layer-view-a.png
docs/images/cif-layer-view-b.png
docs/images/cif-layer-view-c.png
docs/images/dft-evidence-workflow.png
docs/images/software-landscape.png
docs/images/synthetic-bands-dos.png
docs/images/synthetic-convergence.png
```

Run the generator twice and compare the seven SHA-256 values when changing
showcase code. The committed figures must remain byte-deterministic.
