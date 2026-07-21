# Contributing to the Scandium Dataset

We welcome contributions that improve the quality, coverage, or usability of the dataset.

## How to Contribute

### Reporting Issues
- Use the GitHub issue tracker
- Include the entry formula and source_id if reporting a data issue
- Include the release version

### Suggesting Improvements
- Open an issue with the "enhancement" label
- Describe the problem and your proposed solution

### Adding Data
- We do not accept direct additions to the curated dataset
- New sources go through the full validation pipeline
- Contact us to discuss new source integration

### Code Contributions
- Fork the repository
- Create a feature branch
- Submit a PR with a clear description of changes
- Ensure all validation passes

## Development Setup

```bash
git clone https://github.com/Scandium-Labs/Scandium-Dataset
cd Scandium-Dataset
pip install -r requirements.txt
```

## Validation Requirements

Before submitting, ensure:
1. No duplicate entries introduced
2. All new entries pass the validated tier gates
3. Cross-source agreement is documented
4. Tests pass

## Code of Conduct

All contributors must follow our [Code of Conduct](CODE_OF_CONDUCT.md).
