# Quantum ESPRESSO release notes — New in 6.2.1 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `8162e576761007568420b692d703c0f1afe3ff77ef27cc00e20cb653f8d32460`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
New in 6.2.1 version:

  * Spin-polarized SCAN meta-GGA; spin-unpolarized stress for meta-GGA
    (Hsin-Yu Ho and Marcos Calegari Andrade)

  * Interface with Grimme's DFT-D3, as repackaged by Bálint Aradi
    (Miha Gunde and Layla Martins-Samos)
  
  * Phonons for two-dimensional systems (Thibault Sohier et al.)

Problems fixed in 6.2.1 version:

  * PWscf in "driver" mode with i-Pi wasn't working with k-points and
    wasn't honoring options for interpolation - fixed by Przemyslaw Juda
    (r14037)

  * Restart in phonon wasn't working with tetrahedra (r14029)
    and for USPP/PAW at q != 0 (r14034-14036)

  * QM-MM interface with LAMMPS was broken in v.6.2 (r14006-14008)

  * NASTY BUG IN META-GGA WITH LIBXC (tpss, tb09, scan): incorrect results -
    fixed by Hsin-Yu Ho and Marcos Calegari Andrade (r14000, 14004-5, 14027)

  * Electron-phonon with ibrav=0 not working due to a mismatch between
    what is written and what is read in "fildyn" (r13999)

  * Tetrahedra with "old" XML format working again (r13993)

  * Option "-in file" for fermi_proj.x and fermi_velocity.x was not working
    in serial execution; fermisurfer_example/ was missing (r13986). Also:
    Fermi velocity in vfermi.frmsf was 4*celldm(1) times bigger than in
    fermisurfer (reported by Victor Chang, fixed by Mitsuaki Kawamura, r14033)

  * Inconsistent "short name" for DFT was breaking Perdew-Wang pseudopotentials
    (r13975)

  * Yet another problem with last scf step in vc-relax, present since v.6.1: 
    if no atoms of a given kind were present, there was a division by zero
    and a NaN in starting magnetization (reported by Malte Sachs) (r13971)

  * FFT's for ARM libraries were broken (r13956,13959, courtesy Jason Wood)
```
