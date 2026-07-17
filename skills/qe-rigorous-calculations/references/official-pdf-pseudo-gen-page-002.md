# pseudo-gen.pdf — page 2

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/pseudo-gen.pdf
- Retrieved: 2026-07-17T11:53:43+00:00
- Official source SHA-256: `02886b370326652745ebcbdf62ecf29664c9ac8ab661a4537359530f26cc3d23`
- Extracted text SHA-256: `65e1998293602a79c5bcd9cfdf2dda00ea4da658d7e862092ab8ff32531ba229`
- Official Last-Modified: Mon, 08 Dec 2025 21:57:45 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
B Equations for the Troullier-Martins method                                         25


1     Introduction
When I started to do my first first-principle calculation (that is, my first2 -principle
calculation) with Stefano Baroni on CsI under pressure (1985), it became quickly evi-
dent that available pseudopotentials (PP’s) couldn’t do the job. So we generated our
own PP’s. Since that first experience I have generated a large number of PP’s and
people keep asking me new PP’s from time to time. I am happy that ”my” PP’s are
appreciated and used by other people. I don’t think however that the generation of
PP’s is such a hard task that it requires an official (or unofficial) PP wizard to do this.
For this reason I want to share here my (little) experience.
    These notes are written in general but having in mind the capabilities of the atomic
package, included in the Quantum ESPRESSO distribution (http://www.quantum-espresso.org
atomic, mostly written and maintained by Andrea Dal Corso and others, is the evolu-
tion of an older code I maintained for several years. atomic can generate both Norm-
Conserving (NC) [1] and Ultrasoft (US) [2] PP’s, plus Projector Augmented Waves
(PAW) [3] sets. It allows multiple projectors, full relativistic calculations, spin-split
PP’s for spin-orbit calculations. For the complete description of the input of atomic,
please refer to files INPUT LD1.txt and INPUT LD1.html.

1.1    Who needs to generate a pseudopotential?
There are at least three well-known published sets of NC-PP’s: those of Bachelet,
Hamann, and Schlüter [4], those of Gonze, Stumpf, and Scheffler [5], and those of
Goedecker, Teter, and Hutter [6]. Moreover, all major packages for electronic-structure
calculations include a downloadable table of PP’s. One could then wonder what a PP
generation code is useful for. The problem is that sometimes available PP’s will not
suit your needs. For instance, you may want:

    – a better accuracy;

    – PP’s generated with some exotic or new exchange-correlation functional;

    – a different partition of electrons into valence and core;

    – “softer” PP’s (i.e. PP that require a smaller cutoff in plane-wave calculations);

    – PP’s with a core-hole for calculations of X-ray Adsorption Spectra;

    – all-electron wavefunctions reconstruction (requires the knowledge of atomic all-
      electron and pseudo-orbitals used in the generation of PP’s);

or you may simply want to know what is a PP, how to produce PP’s, how reliable they
are.
```
