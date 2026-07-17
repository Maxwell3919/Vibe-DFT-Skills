# user_guide.pdf — page 16

- Official source: https://www.quantum-espresso.org/Doc/user_guide_PDF/user_guide.pdf
- Retrieved: 2026-07-17T11:53:53+00:00
- Official source SHA-256: `1e5b9fb9b22e592cf4efb858c3d5923bd5d4c649d3b64580ea64937c28c0505c`
- Extracted text SHA-256: `53dce9250ec365f16e4367163d7f91e812d932688834f1cf23b976002ad2ed94`
- Official Last-Modified: Tue, 11 Nov 2025 16:28:37 GMT
- Content status: official text extracted from an official PDF page without substantive additions; wrapper metadata added by the mirror script.

```text
2.6.1   Linking in Quantum ESPRESSO
Once installed libxc, the linking with Quantum ESPRESSO can be enabled directly through
the configuration script by adding the two switches --with-libxc and --with-libxc-prefix,
e.g.:

./configure --with-libxc --with-libxc-prefix=’/path/to/libxc/’

By adding the first switch only an automatic search for the libxc folder will be attempted, but
its success is not guaranteed. It is always preferable to specify the second switch too. Optionally,
a third switch can be added, namely --with-libxc-include=’/path/to/libxc/include’,
which specifies the path to the Fortran headers (usually it is not necessary).
     Alternatively, the link to libxc can be activated after the configuration of Quantum
ESPRESSO by modifying the make.inc file in the main folder in this way:

   • add -D LIBXC to DFLAGS

   • add -I/path/to/libxc/include/ to IFLAGS

   • set LD LIBS=-L/path/to/libxc/lib/ -lxcf03 -lxc

Then Quantum ESPRESSO can be compiled as usual.
Note: if the version of libxc is 5.0.0, the last point must be replaced by:

   • set LD LIBS=-L/path/to/libxc/lib/ -lxcf90 -lxc

since the f03 interfaces are no longer available. They have been restored in following releases.
Version 5.0.0 is still usable, but, before compiling Quantum ESPRESSO, a string replacement
is necessary, namely ‘xc f03’ must be replaced with ‘xc f90’ everywhere in the XClib folder.

With CMake: when executing cmake in the build folder, add the following flags:

cmake [....] -DQE_ENABLE_LIBXC=ON -DLIBXC_INCLUDE_DIR=path/to/libxc/include ..

If cmake is not able to find the package you may need to do this: in Quantum ESPRESSO
main folder open CMakeLists.txt and, inside the block if(QE\_ENABLE\_LIBXC), near line
583, add this:

set(ENV{PKG_CONFIG_PATH} "$ENV{PKG\_CONFIG\_PATH}:/path/to/libxc/pkgconfig")

then execute cmake as above and compile.

Note for versions newer than 5.0.0: libxc enforces the Fermi hole curvature by default,
which might lead to inexact results and convergence problems when using some MGGA func-
tionals in Quantum ESPRESSO. This should be switched off by adding the --disable-fhc
flag when compiling libxc.




                                                16
```
