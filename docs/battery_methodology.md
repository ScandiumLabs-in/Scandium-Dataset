# Battery and Electrolyte Subset Methodology

This document explains the methodology behind the Battery and Electrolyte subsets,
justifying their naming and providing a clear rationale for each material family
inclusion.

---

## Battery Subset (82,925 entries)

### Methodology

The Battery subset includes all entries whose `families` list contains at least one
"battery-relevant" family. Relevance is determined by:

1. **Literature prevalence** — is this family studied as a battery material?
2. **Mobile ion presence** — does the composition contain Li, Na, Mg, Ca, Zn, or K?
3. **Electrochemical activity** — can this material function as an electrode or electrolyte?

### Family Relevance

| Family | Battery Relevance | Entries | Justification |
|--------|-------------------|---------|---------------|
| `layered_oxide` | High | 42,015 | LiCoO₂, NMC, NCA — dominant cathode materials |
| `sulfide_sse` | Critical | 16,359 | LGPS, argyrodites — highest-conductivity solid electrolytes |
| `halide_sse` | Critical | 18,803 | Li₃YCl₆, Li₃InCl₆ — emerging high-voltage SSEs |
| `polyanion` | High | 4,519 | LiFePO₄, NASICON-type — commercial cathode materials |
| `nasicon` | Critical | 560 | Na₁₊ₓZr₂SiₓP₃₋ₓO₁₂ — solid electrolyte framework |
| `garnet` | Critical | 23 | Li₇La₃Zr₂O₁₂ (LLZO) — reference solid electrolyte |
| `borohydride` | Medium | 646 | LiBH₄ — lightweight SSE candidates |
| `oxide` | Medium | 11,928 | General oxide cathodes (LiMn₂O₄, etc.) |
| `intermetallic` | Low | 0 | Not included — no mobile ion carrier |
| `unknown` | Low | 0 | Not included — classification unavailable |

### Battery Subset Composition

```
layered_oxide: 42,015 (50.7%)
halide_sse:    18,803 (22.7%)
sulfide_sse:   16,359 (19.7%)
oxide:         11,928 (2.3%)
polyanion:      4,519 (5.4%)
borohydride:      646 (0.8%)
nasicon:          560 (0.7%)
garnet:            23 (0.03%)
```

### Limitations

1. **No experimental conductivity data** — the Battery subset contains only DFT
   computed properties. Ionic conductivity, migration barriers, and cycling
   performance are not present. The Battery label denotes relevance, not
   measured performance.

2. **Family imbalance** — layered oxides dominate (50.7%). Garnets are severely
   undercounted (23 entries). Models trained on this subset may be biased
   toward layered oxide chemistries.

3. **Proxy properties only** — formation energy and band gap are proxies for
   battery performance, not direct measurements. A low formation energy does
   not guarantee good ionic conductivity.

---

## Electrolyte Subset (41,665 entries)

### Methodology

The Electrolyte subset is a stricter filter applied to the Battery subset:

1. Must be **Strict Gold** tier (quality ≥ 80, full provenance, no defects)
2. Must NOT be from OQMD (to avoid non-commercial license concerns)
3. Must be classified as one of: `sulfide_sse`, `halide_sse`, `nasicon`, `garnet`, or `borohydride`
4. Must have `formation_energy_per_atom` available

### Rationale for Excluding Layered Oxides and General Oxides

Layered oxides and general oxides function primarily as cathode materials, not
electrolytes. Solid electrolytes require:
- High ionic conductivity (Li⁺ mobility)
- Wide electrochemical stability window
- Low electronic conductivity

Layered oxides generally fail criterion 3 (they are electronic conductors).
Their inclusion would dilute the electrolyte-specific signal.

### Electrolyte Subset Composition

```
halide_sse:    18,797 (45.1%)
sulfide_sse:   15,701 (37.7%)
nasicon:          548 (1.3%)
borohydride:      596 (1.4%)
oxide:          6,023 (14.5%)  — primarily Li-containing oxides with SSE potential
```

### Intended Use Cases

| Use Case | Recommended Subset | Rationale |
|----------|-------------------|-----------|
| Electrolyte screening | Electrolyte | Strict Gold quality, SSE-focused chemistries |
| Electrode + electrolyte | Battery | Broader coverage including cathodes |
| General property prediction | General (full) | Maximum data diversity |
| Commercial applications | MP-only + JARVIS-only | No OQMD non-commercial restrictions |

### How the Subsets Were Constructed

```python
import json

# Family → battery relevance mapping
BATTERY_FAMILIES = {
    "layered_oxide", "sulfide_sse", "halide_sse",
    "polyanion", "nasicon", "garnet", "borohydride", "oxide"
}

SSE_FAMILIES = {
    "sulfide_sse", "halide_sse", "nasicon", "garnet", "borohydride"
}

with open("entries_final_v3.json") as f:
    entries = json.load(f)

battery = [e for e in entries
           if any(f in BATTERY_FAMILIES for f in e.get("families", []))]

electrolyte = [e for e in battery
               if e.get("strict_gold", {}).get("is_strict_gold", False)
               and e.get("license") != "OQMD-noncommercial"
               and any(f in SSE_FAMILIES for f in e.get("families", []))]
```
