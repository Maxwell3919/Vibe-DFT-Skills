# user_guide.pdf — page 1

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `ebe7e6bfa979d3b27440c35575a0943f431aa9b3389b8a78f77944ff6d4324e2`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
              Guide to building from sources
             Quantum ESPRESSO (v.7.5.0)


Contents
1 Introduction                                                                                    1
  1.1 People . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .    3
  1.2 Contacts . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .    4
  1.3 Guidelines for posting to the mailing list . . . . . . . . . . . . . . . . . . . . . .      5
  1.4 Terms of use . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .    5

2 Installation                                                                                     6
  2.1 Download . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .       6
  2.2 Prerequisites for source compilation . . . . . . . . . . . . . . . . . . . . . . . . .       7
  2.3 Building with CMake . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .        8
  2.4 Building with make . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .       8
       2.4.1 Generalities . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      8
       2.4.2 Environment variables . . . . . . . . . . . . . . . . . . . . . . . . . . . .         9
       2.4.3 Supported architectures . . . . . . . . . . . . . . . . . . . . . . . . . . .        10
       2.4.4 Command-line options . . . . . . . . . . . . . . . . . . . . . . . . . . . .         10
       2.4.5 configure for NVidia GPU’s . . . . . . . . . . . . . . . . . . . . . . . .           11
       2.4.6 Manual configuration . . . . . . . . . . . . . . . . . . . . . . . . . . . . .       12
  2.5 Libraries . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .   12
       2.5.1 BLAS and LAPACK . . . . . . . . . . . . . . . . . . . . . . . . . . . . .            12
       2.5.2 FFT . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      13
       2.5.3 MPI libraries . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      13
       2.5.4 HDF5 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .       13
       2.5.5 Other libraries . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .    14
       2.5.6 In case of trouble . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .     14
  2.6 Libxc library . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .   14
       2.6.1 Linking in Quantum ESPRESSO . . . . . . . . . . . . . . . . . . . . .                15
       2.6.2 Usage . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      16
       2.6.3 Differences between Libxc and internal functionals . . . . . . . . . . . . .         16
       2.6.4 Special cases . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .    17
       2.6.5 XC test . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .      18

                                                 1
```
