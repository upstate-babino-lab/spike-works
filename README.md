# spikeworks

## Update Python environment with needed dependencies

```bash
conda env update -f environment.yml
conda activate spikeworks
```

## To update environment.yml file:

```bash
conda env export --no-builds | grep -v '^prefix:' > environment.yml
```
