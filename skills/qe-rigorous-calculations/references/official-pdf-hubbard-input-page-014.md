# Hubbard_input.pdf — page 14

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/Hubbard_input.pdf
- Retrieved: 2026-07-17T11:53:18+00:00
- Official source SHA-256: `34a3a3db0304500c296adbc8ed0b94e7f602c66d8994f1c6bfcda7eb97b2dd95`
- Extracted text SHA-256: `9e91f3e095da4822416572918db320034866222d17402197ce417deef652ffe1`
- Official Last-Modified: Mon, 08 Dec 2025 21:44:14 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
 Co 0.0000000000     0.0000000000          0.0000000000
 O   0.2604885000   0.2604885000           0.2604885000
 O   0.7395115000   0.7395115000           0.7395115000
 Li 0.5000000000     0.5000000000          0.5000000000
K_POINTS (automatic)
 4 4 4 0 0 0
HUBBARD (ortho-atomic)
V Co-3d Co-3d 1 1 7.70
V Co-3d Co-3p 1 1 1.00
V Co-3p Co-3p 1 1 2.00
V Co-3p Co-3d 1 1 1.00
V Co-3d O-2p   1 19 0.75
V Co-3d O-2s   1 19 0.60
V Co-3p O-2s   1 19 0.50
V Co-3p O-2p   1 19 0.60
...
In this example, we have specified 4 types of interactions per couple. Note that in this exam-
ple we replaced U for Co-3d states using V, as was discussed above (“standard-standard”, i.e.
k=1). In red and blue we highlight two groups of couples. In red we show the first group that
describes 4 types of interactions for the Co atoms. The first line in the red block corresponds
to the on-site U value for Co-3d states. The second line in the red block corresponds to the on-
site interaction between Co-3d and Co-3p states (“standard-background”, i.e. k=2), the third
line in the red block corresponds to the on-site interaction between Co-3p and Co-3p states
(“background-background”, i.e. k=3), and the fourth line in the red block corresponds to the
on-site interaction between Co-3p and Co-3d states (“background-standard”, i.e. k=4). Note
that second and the fourth lines in the red block describe the same thing, so it is ok to drop the
fourth line. Important notice: It is obligatory to keep the order of entries as shown in the
example above: 1) standard-standard, 2) standard-background, 3) background-background, 4)
background-standard. If you do not respect this order then the code will complain and stop.
The second block above (shown in blue) has the same logic as the one we presented above
for the red block. The only difference is that in the blue block we describe various types of
interactions centered on different atoms (thus inter-site, not on-site).

To make things even more complicated, it is possible to specify two Hubbard manifolds in the
“background” channel. The example is shown below.
&control
    calculation=’scf’
    restart_mode=’from_scratch’,
    prefix=’LiCoO2’
    pseudo_dir = ’../pseudo’
    outdir=’./tmp’
 /
 &system
    ibrav = 5, celldm(1) = 9.3705, celldm(4) = 0.83874,
    nat = 4, ntyp = 3, ecutwfc = 50.0, ecutrho = 400.0
 /

                                               14
```
