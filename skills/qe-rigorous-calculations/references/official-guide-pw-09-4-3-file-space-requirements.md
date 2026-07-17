# 4.3 File space requirements

- Official source: https://www.quantum-espresso.org/Doc/pw_user_guide/node17.html
- Retrieved: 2026-07-17T11:51:08+00:00
- Official source SHA-256: `c2bf3dd8660732d81175993b8115dd2e4f5495bba59564e8ba6f441350cdea5c`
- Extracted text SHA-256: `82b0e30126282ae1fd3eb99f7efc3f2def0e0a5712842f8ccfbf8ebfb474937c`
- Official Last-Modified: Mon, 08 Dec 2025 20:49:50 GMT
- Content status: official text extracted from official HTML without substantive additions; wrapper metadata added by the mirror script.

```text
next 

up 

previous 

contents 

Next:

4.4 Parallelization issues

Up:

4 Performances

Previous:

4.2 Memory requirements

  

Contents

4.3 File space requirements

A typical 
pw.x
run will require an amount of temporary disk space in the
order of O double precision complex numbers:

O
= 
N
k
MN
+ 
qN
r1
N
r2
N
r3

where 

q
= 2× 
mixing_ndim
(number of iterations used in 
self-consistency, default value = 8) if 
disk_io
is set to 'high'; q = 0 
otherwise.
```
