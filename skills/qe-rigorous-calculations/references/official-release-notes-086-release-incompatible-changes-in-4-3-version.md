# Quantum ESPRESSO release notes — Incompatible changes in 4.3 version:

- Official source: https://www.quantum-espresso.org/Doc/release-notes
- Retrieved: 2026-07-17T11:53:05+00:00
- Official source SHA-256: `0301dc29c73841d223900c951219766689d9eb89623ed80982149a660489aa8c`
- Extracted text SHA-256: `dcaa86f53f854a1e2621f879774a8a87dcfddc17e363f1d9cf25e5695a129027`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official release-note text split without substantive additions; wrapper metadata added by the mirror script.

```text
Incompatible changes in 4.3 version:

  * pw.x no longer performs NEB calculations. NEB is now computed
    by a separate code, NEB/neb.x . NEB-specific variables are no longer
    read by pw.x; they are read by neb.x after all pw.x variables
  * NEB for cp.x no longer available
  * iq1,iq2,iq3 removed from input in ph.x; use start_q, last_q instead
  * Several global variables having the same meaning and different names
    in CP and in all the other codes (PW) have been given a common name.
    Calls to fft also harmonized to the CP interface fwfft/invfft:
	Old (CP)	New (PW)	Old (PW)	New (CP)
	nnr/nnrx	nrxx		nrx[123]	nr[123]x
	nnrs/nnrsx	nrxxs		nrx[123]s	nr[123]sx
	ngml		ngl		ig[123]		mill (replaces mill_l)
	ngmt		ngm_g
	ngs 		ngms		cft3/cft3s	fwfft/invfft
	ngst 		ngms_g
	g  		gg
	gx		g
	gcuts 		gcutms
	ecutp 		ecutrho
	ecutw 		ecutwfc
	gzero/ng0	gstart
 	np, nm		nl, nlm
 	nps, nms	nls, nlsm
```
