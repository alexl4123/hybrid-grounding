# Newground3: Advanced Grounding for ASP

**Prototype Status:**  
Newground3 is a prototype developed as part of a Master's Thesis. It demonstrates new techniques for grounding in Answer Set Programming (ASP). It is mainly intended for research and testing purposes.
Currently, it works only on Linux systems and may not be fully reliable or polished for other operating systems or production use.

If you don't manage to get it working please open an issue, or write me (alexander.beiser@tuwien.ac.at) an email!

## Overview

Newground3 builds on the Body-Decoupled Grounding (BDG) framework to address the grounding bottleneck in ASP, and is the successor of Newground, and NaGG. It includes:
1. **Hybrid Grounding:** Combines traditional semi-naive grounding with BDG.
2. **Automated Hybrid Grounding:** Uses heuristics to decide when BDG is most effective.
3. **FastFound:** Improves grounding for normal ASP programs (saturation method in prototype).
4. **Lazy-BDG:** Handles cyclic and non-tight rules by shifting some effort to the solving phase (unfound-set method in prototype).

Experiments show that Newground3 performs better than grounders like `gringo` and `idlv` on benchmarks with grounding-heavy scenarios.

---

## Usage

Run Newground3 using:

```bash
python start_heuristic.py [options] [files]
```

### Synopsis:

```
usage: Newground3 [files]

positional arguments:
  files

options:
  -h, --help            show this help message and exit
  --grounding-strategy {full,non-ground-rewrite}
                        Decide whether Newground3 shall be used as a full grounder (full) or in a non-ground rewrite mode (non-ground-rewrite).
  --sota-grounder {gringo,idlv}
                        Decide which state-of-the-art (SOTA) grounder to use ('./gringo' or './idlv.bin' must be present in same directory).
  --output-type {standard-grounder,string,benchmark}
                        For the full grounder output in specific format.
  --debug               Print debug information.
  --enable-logging      Enable additional logging information, e.g., if BDG was used.
  --logging-file LOGGING_FILE
                        Path to the logging file (--enable-logging must be supported as well). Default a file in logs/<FIRST_FILE_NAME>-<CURRENT-DATE-TIME>.log is generated.
  --tw-aware            Use treewidth aware rewritings for rule decomposition (lpopt tool).
  --treewidth-strategy {networkx}
  --cyclic-strategy {use-sota,unfound-set,level-mappings}
  --foundedness-strategy {heuristic,guess,saturation}
                        Decide which BDG version to use - heuristic decides the smalles grounding size automatically, SATURATION prefers FastFound, and GUESS prefers the standard foundedness check.
```



---

## Dependencies

- conda
- Tested with Python 3.12.1
    - Likely that newer and slightly older versions will also work
- SOTA Grounders:
    - `gringo`
    - `idlv.bin`
    - Locally available in this folder (`newground/gringo`, `newground/idlv.bin`)
- Requirements (python):
    - `environment.yml`

```
conda env create -f environment.yml
conda activate newground3
```

---

## Installation

1. Install the `environment.yml` file
2. Use the `compile_all.sh` script for the cython compilation. If errors occur we advise you to manually copy the cython build files to the destinations.


## Examples

We provide you with two very small example files: `test.lp` and `test_2.lp`, and the respective output in `test_output.lp` and `test_2_output.lp`:

```
python start_heuristic_splitter.py --grounding-strategy=non-ground-rewrite test.lp > test_output.lp
```
```
python start_heuristic_splitter.py --grounding-strategy=non-ground-rewrite test_2.lp > test_2_output.lp
```


---

## Known Limitations

- **Linux Only:** This prototype has been tested only on Linux and may not work on other systems.
- **Prototype Status:** The software is experimental and not ready for production.

---

## Acknowledgments

I developed this software as part of my Master's Thesis, see [thesis](https://beiser.eu) for details.

## Supplementary Material:

[Supplementary Material](https://github.com/alexl4123/newground3-supplementary-material-MSC-Thesis)

# Earlier Versions: Newground and NaGG

NaGG is a specialized version of [Newground](https://github.com/alexl4123/newground).
For details and general information see the [documentation](https://www.dbai.tuwien.ac.at/proj/hypar/newground/index.html) page of Newground,
or the respective documentation folder.


