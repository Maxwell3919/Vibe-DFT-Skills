# pw_user_guide.pdf — page 12

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `daf9b43f1ff3126ac02eb864a03db9b5529991f84e7604896acc27a0ee84692b`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
      The closer α is to 1, the better the blip representation. By increasing blip multiplicity,
      or by increasing the plane-wave cutoff, one ought to be able to make α as close to 1 as
      desired. The number of random points used is given by n points for test.

    Finally, note that DFT trial wave functions produced by PWSCF must be generated using
the same pseudopotential as in the subsequent QMC calculation. This requires the use of tools
to switch between the different file formats used by the two codes.
    CASINO uses the ‘CASINO tabulated format’, PWSCF uses the UPF format. See upflib/README.md
for instructions on how to convert between these formats.
    An alternative converter ‘casinogon’ is included in the CASINO distribution which produces
the deprecated GON format but which can be useful when using non-standard grids.

3.6    Socket interface with i-PI
The i-PI universal force engine performs advanced Molecular Dynamics (MD) (such as Path
Integral Molecular Dynamics, Thermodynamic Integration, Suzuki-Chin path integral, Multiple
Time Step molecular dynamics) and other force related computations (see ipi-code.org for
more information about i-PI).
    PWscf users wishing to learn how to use i-PI should refer to the i-PI website.

Practicalities The communication between PWscf and i-PI relies on a socket interface. This
allows running i-PI and PWscf on different computers provided that the two computers have
an Internet connection. Basically, i-PI works as a server waiting for a connection of a suit-
able software (for example PWscf). When this happens, i-PI injects atomic positions and cell
parameters into the software, that will return forces and stress tensor to i-PI.
    The file containing the interface is run_driver.f90. The files socket.c and fsocket.f90
provide the necessary infrastructure to the socket interface.

How to use the i-PI inteface Since the communication goes through the Internet, the
PWscf instance needs to know the address of the i-PI server that can be specified with the
command line option --ipi (or -ipi) followed by the address of the computer running i-PI
and the port number where i-PI is listening, e.g.

pw.x --ipi localhost:3142 -in pw.input > pw.out

If i-PI and PWscf are running on the same machine, a UNIX socket is preferable since allows
faster communications, e.g.

pw.x --ipi socketname:UNIX -in pw.input > pw.out

In the last case, UNIX is a keyword that tells to PWscf to look for an UNIX socket connection
instead of an INET one. More extensive examples and tutorials can be found at ipi-code.org.
The PWscf input file must contain all the information to perform a single point calculation
(calculation = "scf") which are also used to initialize the PWscf run. Thus, it is important
that the PWscf input contains atomic positions and cell parameters which are as close as possible
to those specified in the i-PI input.




                                               12
```
