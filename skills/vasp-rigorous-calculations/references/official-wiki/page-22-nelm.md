# NELM

- Official URL: https://www.vasp.at/wiki/NELM
- Page ID: 22
- Revision ID: 25364
- Retrieved UTC: 2026-07-17T12:41:26+00:00
- Source: official VASP Wiki expanded page text

## Searchable official text

NELM = [integer]
Default: NELM = 60

Description: NELM sets the maximum number of electronic SC (self-consistency) steps.

Normally, there is no need to change the default value: if the self-consistency loop does not converge within 40 steps, it will probably not converge at all. In this case you should reconsider the tags IALGO or ALGO, LSUBROT, and the mixing parameters.

The same stands for ALGO = TIMEEV, as the value is set to be sufficient to ensure numerical stability when propagating in time. If you wish to set it by yourself, be advised that the input value must be greater than 100, otherwise VASP will ignore it and fall to the default settings.

Related tags and articles[edit | edit source]

NELMDL,
NELMIN

Examples that use this tag
