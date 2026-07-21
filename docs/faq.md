# FAQ

### What makes this different from downloading MP/OQMD/JARVIS directly?

Three things: **integration**, **repair**, and **proof**. We don't just concatenate
databases. We deduplicate, repair known artifacts, compute missing metadata,
validate every entry, and — most importantly — we **prove** our quality scores
actually predict label reliability.

### Why 266k entries and not 817k (all OQMD)?

We intentionally filtered OQMD to entries with phase diagrams (FE + EaH). The
full OQMD has 817k entries but many lack computed hull energies. For ML
training, 266k validated entries are more useful than 817k noisy ones.

### Why is OQMD 64% of the dataset?

OQMD contributes more entries because it includes many metastable phases that
are relevant to battery applications. This is a feature, not a bug — but it
means source imbalance should be considered when training models.

### Why is there no score ≥ 90?

Our scoring is intentionally conservative. A score of 90 would require perfect
metadata, perfect geometry, and exceptional novelty. Since all data is DFT-computed
(not experimentally verified), no entry meets this threshold. This is a design
choice that prevents score inflation.

### Why does the Electrolyte edition exclude OQMD?

OQMD entries lacked space groups until recently computed (this release). They
also dominate the general dataset. For the Electrolyte benchmark edition, we
prioritize MP and JARVIS entries which have complete verified metadata.

### How do I cite the dataset?

See [CITATION.cff](../CITATION.cff) or [citation.md](citation.md).

### Can I contribute data?

We do not accept direct data contributions. New sources go through the full
validation pipeline. Contact us if you have a source to integrate.

### When will battery-specific properties (conductivity, migration) be added?

Planned for v4.0. The current focus is on establishing the foundational dataset
as a trusted resource.
