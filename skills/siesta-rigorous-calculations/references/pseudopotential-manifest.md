# SIESTA pseudopotential manifest schema 2.0

Keep runtime manifests in the authorized calculation area. Never commit real project manifests or pseudopotential files to this skill.

```json
{
  "schema_version": "2.0",
  "pseudopotentials": [
    {
      "species_index": 1,
      "format": "psml",
      "expected_sha256": "<64 lowercase hex>",
      "source": "<privacy-safe public URL, DOI, release id, or opaque internal id>",
      "xc_family": "GGA-PBE",
      "relativistic_treatment": "scalar-relativistic",
      "valence_configuration": "3s2-3p2",
      "source_version": "<database/generator release>",
      "validation_id": "<transferability or project validation evidence id>"
    }
  ]
}
```

Requirements:

- Cover each `ChemicalSpeciesLabel` species id exactly once.
- Use only `vps`, `psf`, or `psml`; record the exact file SIESTA is expected to select and hash its bytes.
- Make an implicit basename unambiguous. Multiple `.vps`/`.psf`/`.psml` matches block.
- Resolve all metadata fields; reject placeholders and private absolute paths/hosts/accounts.
- Use `nonrelativistic`, `scalar-relativistic`, or `fully-relativistic` for `relativistic_treatment`.
- Match `xc_family` to the role-ordered
  `<XC.Functional>-<XC.Authors>` identity. The pinned 5.4 table permits:
  - `LDA`/`LSD` with `CA`/`PZ` or `PW92`;
  - `GGA` with `PW91`, `PBE`, `revPBE`, `RPBE`, `WC`, `AM05`, `PBEsol`,
    `PBEJsJrLO`, `PBEJsJrHEG`, `PBEGcGxLO`, `PBEGcGxHEG`, or
    `BLYP`/`LYP`;
  - `VDW` with `DRSLL`/`DF1`, `LMKLL`/`DF2`, `KBM`, `C09`, `BH`, or
    `VV`.
  Role reversal, an incompatible family/author pair, an unknown alias, or an
  unrecognized manifest identity blocks pseudopotential acceptance.
- For PSML, require readable XML and cross-check the embedded LibXC functional ids against `xc_family`; a hash-matched manifest cannot override contradictory embedded metadata.
- A plan declaring `soc`, `spin-orbit`, or `spinorbit`, or an effective direct
  FDF with `Spin spin-orbit` or `Spin spin-orbit+onsite`, requires
  `fully-relativistic` for every species.
- Make `validation_id` point to real external evidence; a label alone does not prove transferability.

The auditor reports local hash/format, recognized PSML XC class, public scientific classifications, and hashes of source/version/validation identities. It does not expose the source string, private location, valence text, or pseudopotential content. Legacy VPS/PSF XC identity remains manifest-bound unless a separately tested parser is added.

A passing manifest gate proves identity and recorded compatibility metadata only. Scientific review must still assess semicore/valence choice, cutoff radii, ghost states, transferability, nonlinear core correction, and observable-specific validation.
