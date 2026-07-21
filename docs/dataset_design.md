# Dataset Design

## Schema

Every entry in the Scandium Dataset follows this schema:

```python
{
    # Identity
    "source": str,            # "mp", "oqmd", or "jarvis"
    "source_id": str,         # Original database ID
    "formula": str,           # Reduced formula
    
    # Properties
    "formation_energy_per_atom": float,   # eV/atom
    "energy_above_hull": float,           # eV/atom (null for JARVIS)
    "band_gap": float,                    # eV
    
    # Structure
    "structure_json": str,    # JSON-encoded pymatgen Structure
    "nsites": int,
    "volume": float,          # Å³
    "density": float,         # g/cm³
    "space_group": int,       # International number
    "space_group_symbol": str,
    
    # Composition
    "elements": [str],        # Element list (with repetitions)
    "anions": [str],          # Anion elements
    
    # Classification
    "families": [str],        # Material families
    "carrier_elements": [str], # Mobile ions (Li, Na, etc.)
    "is_metal": bool,
    "magnetic_ordering": str or None,
    "is_experimental": bool,
    
    # Quality
    "quality_score": float,   # 0-100 composite
    "quality_sub_scores": {
        "geometry": int,      # 0-25
        "dft": int,           # 0-20
        "metadata": int,      # 0-15
        "novelty": int,       # 0-20
        "chemical": int       # 0-15 (yes, sums to 95 not 100)
    },
    "quality_flags": [str],
    
    # Tiering
    "tier": str,              # "gold", "validated", "raw"
    "tier_gates": {str: bool},
    "strict_gold": {
        "is_strict_gold": bool,
        "gates": {str: bool},
        "confidence_calibration": {...}
    },
    
    # Provenance
    "provenance": {
        "source": str,
        "source_id": str,
        "checksum": str,
        "repairs_applied": [dict],
        "dedup_resolution": dict or None,
        "tier_assignment": dict,
        "version": str
    },
    
    # Dedup
    "duplicate_group": int or None,
    
    # References
    "references": [str],
    "source_weight": float,   # 1.0 for all entries
}
```

## Source Integration

### Materials Project (MP)
- **API**: pymatgen MPRester
- **Filter**: `chemsys` includes Li, Na, Mg, Ca, Zn, Al, K
- **Completeness**: 100% for all metadata fields
- **Count**: 69,279 entries

### OQMD
- **API**: jarvis-tools `data("oqmd_3d_no_cfid")`
- **Count**: 171,780 entries
- **Known issues**: All resolved via repair pipeline

### JARVIS-DFT
- **API**: jarvis-tools `data("jarvis_dft_3d")`
- **Count**: 25,673 entries
- **Limitation**: No energy_above_hull (fundamental)

## Family Classification

Each entry is classified into one or more material families based on
element composition:

| Family | Criteria | Battery Relevance |
|--------|----------|------------------|
| intermetallic | No O, S, F, Cl, Br, I | Low |
| layered_oxide | Has O + Li/Na + transition metal | High |
| sulfide_sse | Has S + Li/Na | Critical |
| halide_sse | Has F/Cl/Br/I + Li/Na | Critical |
| polyanion | Has O + P/S + Li/Na | High |
| nasicon | Na/Zr/Si/P pattern | Critical |
| garnet | Li/La/Zr pattern | Critical |
| borohydride | Has B + H + Li/Na | Medium |
| oxide | Has O, not otherwise classified | Medium |

## Three Editions

| Edition | Scope | Entries |
|---------|-------|---------|
| General | All entries | 266,732 |
| Battery | Battery families only | 82,925 |
| Electrolyte | Strict Gold, battery, no OQMD | 41,665 |
