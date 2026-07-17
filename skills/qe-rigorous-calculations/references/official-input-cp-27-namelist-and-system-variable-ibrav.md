# INPUT_CP — NAMELIST: &SYSTEM — Variable: ibrav

- Official source: https://www.quantum-espresso.org/Doc/INPUT_CP.txt
- Retrieved: 2026-07-17T11:48:58+00:00
- Official source SHA-256: `f38f5ca5bd6eef5196486d9b4f22c5e14c3915662b8a367a10fae12ca6e77055`
- Extracted text SHA-256: `b83ad750ca7be481394d3ecaa505f1c3e30798a4a29e7dd306b866439cf3b7bd`
- Official Last-Modified: Tue, 11 Nov 2025 16:30:05 GMT
- Content status: official TXT text split without substantive additions; wrapper metadata added by the mirror script.

```text
   +--------------------------------------------------------------------
   Variable:       ibrav
   
   Type:           INTEGER
   Status:         REQUIRED
   Description:    Bravais-lattice index. If ibrav /= 0, specify EITHER
                     [ celldm(1)-celldm(6) ] OR [ A,B,C,cosAB,cosAC,cosBC ]
                     but NOT both. The lattice parameter "alat" is set to
                     alat = celldm(1) (in a.u.) or alat = A (in Angstrom);
                     see below for the other parameters.
                     For ibrav=0 specify the lattice vectors in CELL_PARAMETER,
                     optionally the lattice parameter alat = celldm(1) (in a.u.)
                     or = A (in Angstrom), or else it is taken from CELL_PARAMETERS
                   
                   ibrav      structure                   celldm(2)-celldm(6)
                                                        or: b,c,cosbc,cosac,cosab
                     0          free
                         crystal axis provided in input: see card CELL_PARAMETERS
                   
                     1          cubic P (sc)
                         v1 = a(1,0,0),  v2 = a(0,1,0),  v3 = a(0,0,1)
                   
                     2          cubic F (fcc)
                         v1 = (a/2)(-1,0,1),  v2 = (a/2)(0,1,1), v3 = (a/2)(-1,1,0)
                   
                     3          cubic I (bcc)
                         v1 = (a/2)(1,1,1),  v2 = (a/2)(-1,1,1),  v3 = (a/2)(-1,-1,1)
                    -3          cubic I (bcc), more symmetric axis:
                         v1 = (a/2)(-1,1,1), v2 = (a/2)(1,-1,1),  v3 = (a/2)(1,1,-1)
                   
                     4          Hexagonal and Trigonal P        celldm(3)=c/a
                         v1 = a(1,0,0),  v2 = a(-1/2,sqrt(3)/2,0),  v3 = a(0,0,c/a)
                   
                     5          Trigonal R, 3fold axis c        celldm(4)=cos(gamma)
                         The crystallographic vectors form a three-fold star around
                         the z-axis, the primitive cell is a simple rhombohedron:
                         v1 = a(tx,-ty,tz),   v2 = a(0,2ty,tz),   v3 = a(-tx,-ty,tz)
                         where c=cos(gamma) is the cosine of the angle gamma between
                         any pair of crystallographic vectors, tx, ty, tz are:
                           tx=sqrt((1-c)/2), ty=sqrt((1-c)/6), tz=sqrt((1+2c)/3)
                    -5          Trigonal R, 3fold axis <111>    celldm(4)=cos(gamma)
                         The crystallographic vectors form a three-fold star around
                         <111>. Defining a' = a/sqrt(3) :
                         v1 = a' (u,v,v),   v2 = a' (v,u,v),   v3 = a' (v,v,u)
                         where u and v are defined as
                           u = tz - 2*sqrt(2)*ty,  v = tz + sqrt(2)*ty
                         and tx, ty, tz as for case ibrav=5
                         Note: if you prefer x,y,z as axis in the cubic limit,
                               set  u = tz + 2*sqrt(2)*ty,  v = tz - sqrt(2)*ty
                               See also the note in Modules/latgen.f90
                   
                     6          Tetragonal P (st)               celldm(3)=c/a
                         v1 = a(1,0,0),  v2 = a(0,1,0),  v3 = a(0,0,c/a)
                   
                     7          Tetragonal I (bct)              celldm(3)=c/a
                         v1=(a/2)(1,-1,c/a),  v2=(a/2)(1,1,c/a),  v3=(a/2)(-1,-1,c/a)
                   
                     8          Orthorhombic P                  celldm(2)=b/a
                                                                celldm(3)=c/a
                         v1 = (a,0,0),  v2 = (0,b,0), v3 = (0,0,c)
                   
                     9          Orthorhombic base-centered(bco) celldm(2)=b/a
                                                                celldm(3)=c/a
                         v1 = (a/2, b/2,0),  v2 = (-a/2,b/2,0),  v3 = (0,0,c)
                    -9          as 9, alternate description
                         v1 = (a/2,-b/2,0),  v2 = (a/2, b/2,0),  v3 = (0,0,c)
                   
                    10          Orthorhombic face-centered      celldm(2)=b/a
                                                                celldm(3)=c/a
                         v1 = (a/2,0,c/2),  v2 = (a/2,b/2,0),  v3 = (0,b/2,c/2)
                   
                    11          Orthorhombic body-centered      celldm(2)=b/a
                                                                celldm(3)=c/a
                         v1=(a/2,b/2,c/2),  v2=(-a/2,b/2,c/2),  v3=(-a/2,-b/2,c/2)
                   
                    12          Monoclinic P, unique axis c     celldm(2)=b/a
                                                                celldm(3)=c/a,
                                                                celldm(4)=cos(ab)
                         v1=(a,0,0), v2=(b*cos(gamma),b*sin(gamma),0),  v3 = (0,0,c)
                         where gamma is the angle between axis a and b.
                   -12          Monoclinic P, unique axis b     celldm(2)=b/a
                                                                celldm(3)=c/a,
                                                                celldm(5)=cos(ac)
                         v1 = (a,0,0), v2 = (0,b,0), v3 = (c*cos(beta),0,c*sin(beta))
                         where beta is the angle between axis a and c
                   
                    13          Monoclinic base-centered        celldm(2)=b/a
                                                                celldm(3)=c/a,
                                                                celldm(4)=cos(gamma)
                         v1 = (  a/2,         0,                -c/2),
                         v2 = (b*cos(gamma), b*sin(gamma),       0  ),
                         v3 = (  a/2,         0,                 c/2),
                         where gamma=angle between axis a and b projected on xy plane
                   
                   -13          Monoclinic base-centered        celldm(2)=b/a
                                (unique axis b)                 celldm(3)=c/a,
                                                                celldm(5)=cos(beta)
                         v1 = (  a/2,       b/2,             0),
                         v2 = ( -a/2,       b/2,             0),
                         v3 = (c*cos(beta),   0,   c*sin(beta)),
                         where beta=angle between axis a and c projected on xz plane
                    IMPORTANT NOTICE: until QE v.6.4.1, axis for ibrav=-13 had a
                    different definition: v1(old) = v2(now), v2(old) = -v1(now)
                   
                    14          Triclinic                       celldm(2)= b/a,
                                                                celldm(3)= c/a,
                                                                celldm(4)= cos(bc),
                                                                celldm(5)= cos(ac),
                                                                celldm(6)= cos(ab)
                         v1 = (a, 0, 0),
                         v2 = (b*cos(gamma), b*sin(gamma), 0)
                         v3 = (c*cos(beta),  c*(cos(alpha)-cos(beta)cos(gamma))/sin(gamma),
                              c*sqrt( 1 + 2*cos(alpha)cos(beta)cos(gamma)
                                        - cos(alpha)^2-cos(beta)^2-cos(gamma)^2 )/sin(gamma) )
                     where alpha is the angle between axis b and c
                            beta is the angle between axis a and c
                           gamma is the angle between axis a and b
   +--------------------------------------------------------------------
   
   ///---
      EITHER:
      
```
