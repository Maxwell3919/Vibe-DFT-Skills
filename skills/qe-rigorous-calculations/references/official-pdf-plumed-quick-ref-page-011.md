# plumed_quick_ref.pdf — page 11

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/plumed_quick_ref.pdf
- Retrieved: 2026-07-17T11:53:37+00:00
- Official source SHA-256: `a5c2a829e53a280183e491dba76248bb2cf4be7a775fb97ab03e8f86af15b09f`
- Extracted text SHA-256: `6daff0d606234e273090dbbd101074bc896d9bc02f1181d227af50c49a71d0e5`
- Official Last-Modified: Mon, 08 Dec 2025 21:59:52 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
   100.000         3.507739014          5.800326723          0.001994356          0.000000000
                   0.000000000          0.000000000          0.000000000

   In the first line there is a simple remainder to the elements that you have in each
column. Namely time first (in a.u. by default in Quantum ESPRESSO), then the
value of the two CVs followed by the various additional potential energies introduced
by PLUMED. The fourth column is the bias potential, the wall potential is in the fifth
column and the external potential is in the last. Now you can plot the evolution of the
CVs with gnuplot by using the command p "./COLVAR" u 1:2 t "CV1" ,"" u 1:3
t "CV2" and youll get something like Fig. 2. If you want to understand how the CVs
are related then you may use the command p "./COLVAR" u 2:3 with gnuplot that
results in a plot like that in Fig. 3.




                         Figure 2: The time evolution of CVs


   Beside the usual COLVAR file, when you run a metadynamics calculation you get an
additional file called HILLS which contains a list of the Gaussians deposited during the
simulation. In the example above, this file looks like:

    40.000         3.483516729         5.817608411           0.300000000          0.300000000
                   0.001000000      0.000
    80.000         3.498291622         5.807005696           0.300000000          0.300000000
                   0.001000000      0.000
   120.000         3.519061248         5.792237732           0.300000000          0.300000000
                   0.001000000      0.000
   160.000         3.547107311         5.772092610           0.300000000          0.300000000
                   0.001000000      0.000

                                          11
```
