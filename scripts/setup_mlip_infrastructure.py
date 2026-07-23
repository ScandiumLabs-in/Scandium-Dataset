"""Set up MLIP infrastructure for high-throughput migration barrier computation.

Installs and validates MLIP tools for nudged elastic band (NEB) calculations:
  - CHGNet: universal crystal Hamiltonian Graph neural Network
  - MACE-MP-0: MACE architecture trained on Materials Project trajectories
  - M3GNet: universal potential from Materials Project
  - Orb-v3: Orbital-based MLIP

This script:
  1. Checks what's installed
  2. Attempts installation of missing packages
  3. Validates each potential on a test structure
  4. Generates a configuration file for the NEB pipeline

Usage:
    python scripts/setup_mlip_infrastructure.py
    python scripts/setup_mlip_infrastructure.py --check-only
    python scripts/setup_mlip_infrastructure.py --install
"""
import argparse, os, sys, subprocess, json, warnings
from pathlib import Path

MLIP_PACKAGES = {
    "chgnet": "chgnet",
    "mace": "mace-torch",
    "matgl": "matgl",
    "orb": "orb-models",
}

TEST_STRUCTURE = """
{
    "@module": "pymatgen.core.structure",
    "@class": "Structure",
    "lattice": {"matrix": [[3.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 3.0]], "pbc": [true, true, true]},
    "sites": [
        {"species": [{"element": "Li", "occu": 1}], "abc": [0.0, 0.0, 0.0]},
        {"species": [{"element": "Cl", "occu": 1}], "abc": [0.5, 0.5, 0.5]}
    ]
}
"""


def check_installed():
    """Check which MLIP packages are installed."""
    results = {}
    for name, pkg in MLIP_PACKAGES.items():
        try:
            __import__(name.replace("-", "_"))
            results[name] = "installed"
        except ImportError:
            try:
                __import__(pkg.replace("-", "_"))
                results[name] = "installed"
            except ImportError:
                results[name] = "not found"
    return results


def install_packages(packages):
    """Install MLIP packages via pip."""
    for name, pkg in packages.items():
        print(f"  Installing {pkg}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"    {name}: installed")
        else:
            print(f"    {name}: failed — {result.stderr[-200:]}")


def validate_chgnet(structure_dict):
    """Validate CHGNet can predict on test structure."""
    import json
    from pymatgen.core import Structure
    from chgnet.model import CHGNet
    from chgnet.utils import write_structures_to_POSCAR
    
    struct = Structure.from_dict(structure_dict)
    model = CHGNet.load()
    prediction = model.predict_structure(struct)
    return {
        "energy": float(prediction["e"]),
        "forces_shape": list(prediction["f"].shape),
    }


def validate_mace(structure_dict):
    """Validate MACE can predict on test structure."""
    import torch
    from mace.calculators import MACECalculator
    from ase.io import read
    from pymatgen.core import Structure
    from pymatgen.io.ase import AseAtomsAdaptor
    
    struct = Structure.from_dict(structure_dict)
    atoms = AseAtomsAdaptor.get_atoms(struct)
    
    calc = MACECalculator(model_path="medium", device="cpu")
    atoms.set_calculator(calc)
    energy = atoms.get_potential_energy()
    forces = atoms.get_forces()
    
    return {
        "energy": float(energy),
        "forces_shape": list(forces.shape),
    }


def main():
    parser = argparse.ArgumentParser(description="MLIP infrastructure setup")
    parser.add_argument("--check-only", action="store_true",
                        help="Check installed packages only")
    parser.add_argument("--install", action="store_true",
                        help="Install missing MLIP packages")
    parser.add_argument("--validate", action="store_true",
                        help="Validate installed potentials on test structure")
    args = parser.parse_args()
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    print("=" * 60)
    print("  MLIP INFRASTRUCTURE SETUP")
    print("  High-throughput migration barrier computation pipeline")
    print("=" * 60)
    
    # Check installed packages
    print("\n  Checking installed MLIP packages...")
    installed = check_installed()
    for name, status in installed.items():
        print(f"    {name:12s}: {status}")
    
    if args.install:
        to_install = {k: v for k, v in MLIP_PACKAGES.items() if installed[k] == "not found"}
        if to_install:
            print(f"\n  Installing {len(to_install)} packages...")
            install_packages(to_install)
        else:
            print("\n  All packages already installed.")
    
    if args.validate:
        print("\n  Validating potentials...")
        struct_dict = json.loads(TEST_STRUCTURE)
        
        if installed.get("chgnet") == "installed":
            try:
                result = validate_chgnet(struct_dict)
                print(f"    CHGNet: OK (energy={result['energy']:.3f} eV)")
            except Exception as e:
                print(f"    CHGNet: validation failed — {str(e)[:80]}")
        
        if installed.get("mace") == "installed":
            try:
                result = validate_mace(struct_dict)
                print(f"    MACE: OK (energy={result['energy']:.3f} eV)")
            except Exception as e:
                print(f"    MACE: validation failed — {str(e)[:80]}")
    
    # Generate config file
    if not args.check_only:
        config = {
            "potentials": installed,
            "pipeline": {
                "bvse_barrier_threshold": 0.5,
                "mlip_neb_grid": [5, 5, 5],
                "mlip_neb_spring_constant": 5.0,
                "mlip_neb_fmax": 0.05,
                "mlip_neb_steps": 500,
            },
            "target_subset": "gold_battery_li",
            "description": "Li-containing Gold-tier battery-family entries",
        }
        
        config_path = BASE_DIR / "configs" / "mlip_pipeline.json"
        print(f"\n  Writing config to {config_path}...")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
    
    # Print next steps
    print(f"\n{'─' * 60}")
    print("  NEXT STEPS")
    print(f"  {'─' * 60}")
    print("""
  1. Install MLIP packages:
     pip install chgnet mace-torch matgl orb-models
     
  2. Run BVSE pre-filter on Li/Na entries:
     python scripts/compute_bvse_barriers.py --subset gold --limit 50000
     
  3. Run MLIP-NEB on BVSE-filtered subset:
     python scripts/run_mlip_neb_pipeline.py --input dataset/bvse_filtered.json
     
  4. Update sse_candidate_score with full 5 gates:
     python scripts/compute_sse_candidate_score.py
  """)
    print("=" * 60)


if __name__ == "__main__":
    main()
