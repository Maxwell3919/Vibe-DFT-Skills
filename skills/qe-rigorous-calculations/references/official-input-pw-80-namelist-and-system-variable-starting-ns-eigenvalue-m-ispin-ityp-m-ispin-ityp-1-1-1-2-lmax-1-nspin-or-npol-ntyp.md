# INPUT_PW — NAMELIST: &SYSTEM — Variable: starting_ns_eigenvalue(m,ispin,ityp), (m,ispin,ityp)=(1,1,1) ... (2*lmax+1,nspin or npol,ntyp)

- Official source: https://www.quantum-espresso.org/Doc/INPUT_PW.txt
- Retrieved: 2026-07-17T11:49:47+00:00
- Official source SHA-256: `344932e399030687217a5a311ab4504a7b21a6a2281680dfa92074aec29c491d`
- Extracted text SHA-256: `af06223693ede7ba3a85716c59d1506f2d3cbe1c23ba6dca6836748eb9eee860`
- Official Last-Modified: Tue, 11 Nov 2025 16:27:52 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       starting_ns_eigenvalue(m,ispin,ityp), (m,ispin,ityp)=(1,1,1) ... (2*lmax+1,nspin or npol,ntyp)
   
   Type:           REAL
   Default:        -1.d0 that means NOT SET
   Description:    In the first iteration of an DFT+U run it overwrites
                   the m-th eigenvalue of the ns occupation matrix for the
                   ispin component of atomic species ityp.
                   For the noncollinear case, the ispin index runs up to npol=2
                   The value lmax  is given by the maximum angular momentum
                   number to which the Hubbard U is applied.
                   Leave unchanged eigenvalues that are not set.
                   This is useful to suggest the desired orbital occupations
                   when the default choice takes another path.
   +--------------------------------------------------------------------
   
```
