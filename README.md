# CMS Barrel Timing Layer (BTL) Module Analysis @ Caltech

Authors:
- Paul Simmerling, [psimmerl@caltech.edu](mailto:psimmerl@caltech.edu)
- Alex Albert
- Zichun Hao
- Kai Svensson
- Adolf Bornheim


# How to run this analysis
---

Notebooks (used to interact with & visualize data):
- `analyze_histos.ipynb`
    - use this to histograms generated from `qaqc_jig`'s `analyze-waveforms`

Tools (for terminal):
- `quick_draw.py`
- `makeLightYieldPlots.py`

## Git LFS

For storing `.root` and `.hdf5` files. Maxmimum size is 2GB, GitHub otherwise limits us at 50 MiB.

https://docs.github.com/en/repositories/working-with-files/managing-large-files/installing-git-large-file-storage



## Python Environment
Use conda to create the environment

```bash
conda create --name qaqc --channel conda-forge python root hdf5 numpy numba scipy matplotlib pandas jupyter
source env.sh # or `conda activate qaqc`
```

