from __future__ import annotations

import importlib.metadata
import shutil
from typing import Any


EXTERNAL_TOOLS = {
    "qe.bands": "bands.x",
    "qe.plotband": "plotband.x",
    "qe.dos": "dos.x",
    "qe.projwfc": "projwfc.x",
    "qe.sumpdos": "sumpdos.x",
    "qe.pp": "pp.x",
    "qe.average": "average.x",
    "qe.q2r": "q2r.x",
    "qe.matdyn": "matdyn.x",
    "qe.dynmat": "dynmat.x",
    "qe.lambda": "lambda.x",
    "qe.alpha2f": "alpha2f.x",
    "qe.epsilon": "epsilon.x",
    "cp2k.input_lint": "cp2klint",
    "cp2k.output_parse": "cp2kparse",
    "cp2k.bands_convert": "cp2k_bs2csv",
    "cp2k.pdos_convolve": "cp2k_pdos",
    "cp2k.restart_trajectory_clean": "xyz_restart_cleaner",
    "vasp.vaspkit": "vaspkit",
    "charge.bader": "bader",
    "charge.critic2": "critic2",
    "phonon.phonopy": "phonopy",
    "bands.sumo": "sumo-bandplot",
    "bands.pyprocar": "pyprocar",
    "wannier.wannier90": "wannier90.x",
}

PYTHON_PACKAGES = (
    "numpy",
    "scipy",
    "pandas",
    "matplotlib",
    "ase",
    "pymatgen",
    "py4vasp",
    "h5py",
    "xarray",
    "spglib",
    "seekpath",
)


def detect_capabilities() -> dict[str, Any]:
    external = {}
    for role, command in EXTERNAL_TOOLS.items():
        path = shutil.which(command)
        external[role] = {"command": command, "available": path is not None, "path": path}
    from .vesta import resolve_vesta_executable

    vesta_path = resolve_vesta_executable()
    external["visualization.vesta"] = {
        "command": "VESTA",
        "available": vesta_path is not None,
        "path": str(vesta_path) if vesta_path is not None else None,
    }
    python = {}
    for package in PYTHON_PACKAGES:
        try:
            version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            version = None
        python[package] = {"available": version is not None, "version": version}
    return {"schema_version": "1.0", "external_tools": external, "python_packages": python}
