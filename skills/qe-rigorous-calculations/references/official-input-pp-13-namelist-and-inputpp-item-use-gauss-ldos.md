# INPUT_PP — NAMELIST: &INPUTPP — Item: use_gauss_ldos

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PP.html
- Retrieved: 2026-07-17T11:49:40+00:00
- Official source SHA-256: `482dc70016a4638b18eca0219e56754e09fa195524a55decd6df3e6fbc5efd1c`
- Extracted text SHA-256: `5b1bddb74a9e4d118a91631a8e8d5f2e2743f12714faf7aae66513ba0866b1a4`
- Official Last-Modified: Tue, 09 Dec 2025 07:41:05 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text


use_gauss_ldos

LOGICAL

Default:

.false.

Status:

OPTIONAL

If .true., gaussian broadening (ngauss=0) is used for LDOS calculation.

Defaults .false., in which case the broadening scheme
of the pw.x calculation will be used.

[
Back to Top
]

ELSEIF 
plot_num=5
:

Options for STM images (plot_num=5):
```
