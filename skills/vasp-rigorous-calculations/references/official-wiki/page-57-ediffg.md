# EDIFFG

- Official URL: https://www.vasp.at/wiki/EDIFFG
- Page ID: 57
- Revision ID: 32794
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

EDIFFG = [real]
Default: EDIFFG = EDIFF×10

Description: EDIFFG defines the break condition for the ionic relaxation loop.

When EDIFFG is positive, the relaxation is stopped when the change of the total energy is smaller than EDIFFG between two ionic steps.

When EDIFFG is negative, the relaxation is stopped when the norms of all the forces are smaller than |EDIFFG|. This is usually a more convenient setting.

If EDIFFG = 0, the ionic relaxation is stopped after NSW steps.

Warning: EDIFFG does not apply to molecular-dynamics simulations.

Tip: You can get information at each electronic step using NWRITE = 2,3.

Related tags and articles[edit | edit source]

EDIFF, NWRITE

Examples that use this tag
