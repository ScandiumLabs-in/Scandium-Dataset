# License Breakdown

The Scandium Dataset is a **multi-source compilation** with **different licenses applying to different entries**. There is no single license that covers the entire dataset.

## Per-Source License

| Source | Entries | License | Commercial Use | Redistribution |
|--------|---------|---------|----------------|----------------|
| Materials Project (MP) | 69,279 (26.0%) | **CC BY 4.0** | ✅ Yes | ✅ With attribution |
| JARVIS-DFT | 25,673 (9.6%) | **CC0 1.0** (Public Domain) | ✅ Yes | ✅ Unlimited |
| OQMD | 171,780 (64.4%) | **OQMD Non-Commercial** | ❌ No | ✅ Non-commercial with attribution |

## How to Find the License for a Given Entry

Every entry in the dataset includes a `license` field. Filter by it:

```python
import json

with open("entries_final_v3.json") as f:
    entries = json.load(f)

# Get only commercially-safe entries (MP + JARVIS)
commercial_safe = [e for e in entries if e["license"] != "OQMD-noncommercial"]
print(f"{len(commercial_safe)} entries are commercially safe")
```

## Commercial-Safe Subset

If you need a dataset free of OQMD non-commercial restrictions, use only:

- **MP entries** (CC BY 4.0) — 69,279 entries
- **JARVIS entries** (CC0) — 25,673 entries

**Total: 94,952 entries (35.6% of full dataset)**

## License Texts

### CC BY 4.0
Applies to: Materials Project entries + Scandium processing code/documentation
- https://creativecommons.org/licenses/by/4.0/
- Attribution required to "Materials Project" (Jain et al., APL Materials, 2013)

### CC0 1.0 (Public Domain)
Applies to: JARVIS-DFT entries
- https://creativecommons.org/publicdomain/zero/1.0/
- NIST Public Domain. No attribution required (though appreciated).

### OQMD Non-Commercial
Applies to: OQMD entries
- https://oqmd.org/about
- Free for non-commercial use only
- Attribution required to "OQMD" (Saal et al., JOM, 2013; Kirklin et al., npj Comp. Mater., 2015)

## Important Notes

1. **The merged file is NOT uniformly CC-BY-4.0.** If you redistribute the merged dataset, you must respect the most restrictive license present (OQMD non-commercial).
2. **Do not use the top-level "cc-by-4.0" badge** as a substitute for reading this breakdown.
3. **Scandium processing, quality scoring, and documentation** are CC BY 4.0 regardless of source.
4. This breakdown is not legal advice. Consult a lawyer for your specific use case.
