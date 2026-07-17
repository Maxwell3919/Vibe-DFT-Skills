# pw_user_guide.pdf — page 13

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pw_user_guide.pdf
- Retrieved: 2026-07-17T11:53:45+00:00
- Official source SHA-256: `a94c460a64bf1faec21ce6b6de0ff5d6833b8188dc5af87c5f36103816644cc3`
- Extracted text SHA-256: `e65c811775f09028b35846f2c112e2ca617a829d2b2ac41e4a2a57273a1f4dd4`
- Official Last-Modified: Mon, 08 Dec 2025 21:27:46 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
Advanced i-PI usage For more advanced users, calculation flags can be changed on-the-fly
by parsing a single binary-encoded integer to QE through the i-PI socket. That gives users the
flexibility to define what properties to be calculated. For example, if only a single SCF cycle is
needed, traditionally run_driver.f90 would be set to calculate not only the potential energy,
but also forces, stresses and initialize g-vectors. With the binary-integer encoded flags, now
one can turn flags on and off as necessary to speed up their code flow.
    The sequence of flags that is currently accepted is: SCF, forces, stresses, variable-cell and
ensembles. The latter is only available if QE has been compiled against BEEF-vdW XC. For
a SCF and forces-only calculation, that would corresponds to a 11000 sequence, which has a
24 decimal representation. The QE side of the i-PI socket expects the equivalent-decimal+1;
therefore, for a 11000 calculation, the integer 25 would have to be parsed to the driver_init
subroutine in run_driver.f90. If any number less-than or equal-to 1 is parsed to QE, it falls
back to its standard i-PI mode.
    Currently, the QE i-PI interface can only reside in three different states: ”NEEDINIT”,
”READY” or ”HAVEDATA”. Whenever the socket sends a ”STATUS” message to QE, it
responds back with its current status. A simple calculation sequence of events would be: (1)
an ”STATUS” message is received, QE sends back ”NEEDINIT”, (2) an ”INIT” message is
received, QE waits for three data packets, (i) an integer that identifies the client on the other
side of the socket, (ii) the flag-encoded integer mentioned above, which can be used to change
calculation settings, and (iii) an initialization string. QE then changes its status to ”READY”.
(3) The server sends a ”POSDATA” message and QE then expects a sequence of variables
depending on the calculation settings; the default being: a 3-by-3 matrix with cell and 3-by-3
marix with its inverse (if lmovecell is .TRUE.) and a (# of atoms)-by-3 position matrix. QE
proceeds and computes all active properties (e.g. SCF, forces, stresses, etc.) and change its
status to ”HAVEDATA” and expects a (4) ”GETFORCE” message from the socket. Once it is
received, (5) QE sends back (i) a float with the potential energy, (ii) an integer with the total
number of atoms, (iii) a (# of atoms)-by-3 matrix with forces (if lforce is .TRUE.), (iv) a
9-element-virial tensor (if lstres is .TRUE.). QE goes back to ”NEEDINIT” status. The other
side of socket should be able to compute new positions and cell coordinates (if lmovecell is
.TRUE.) and start the cycle again from (1).


4     Performances
4.1    Execution time
The following is a rough estimate of the complexity of a plain scf calculation with pw.x, for
NCPP. USPP and PAW give raise additional terms to be calculated, that may add from a
few percent up to 30-40% to execution time. For phonon calculations, each of the 3Nat modes
requires a time of the same order of magnitude of self-consistent calculation in the same system
(possibly times a small multiple). For cp.x, each time step takes something in the order of
Th + Torth + Tsub defined below.
   The time required for the self-consistent solution at fixed ionic positions, Tscf , is:

                                     Tscf = Niter Titer + Tinit

where Niter = number of self-consistency iterations (niter), Titer = time for a single iteration,
Tinit = initialization time (usually much smaller than the first term).

                                                13
```
