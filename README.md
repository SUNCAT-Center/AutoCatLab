# AutoCatLab

AutoCatLab is a python library which seamlessly perform high-throughput calculations both for BULK and surfaces (e.g DFT and DFT+ICOHP ) along with all data analysis which is config Driven.
This repository contains various script files that are requires to perform VASP calculations ([VASP with ASE interface)](https://wiki.fysik.dtu.dk/ase/ase/calculators/vasp.html#introduction)
and [materials project](https://materialsproject.org/) related queries.

Atomistic simulation environment [(ASE)](https://wiki.fysik.dtu.dk/ase/) is an open source python library which help to setting up, manipulate, run, visualize and analyzing atomistic simulations.
It's interface makes it possible to use VASP as a calculator in ASE, 
and also to use ASE as a post-processing tool for an already performed VASP  calculations.

Following are some brief explanation for different functionalities and their related calculations. 

## 🚀 Quick Install

```bash
pip3 install git+https://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@github.com/ruchikamahajan66/autocatlab_v3.git 
```

## 📋 Prerequisites

This package requires:
* [PyTorch](https://pytorch.org/)
* [scikit-learn](https://scikit-learn.org/stable/)
* [pymatgen](https://pymatgen.org/)
* [ASE](https://wiki.fysik.dtu.dk/ase/) and [ASE DB](https://wiki.fysik.dtu.dk/ase/ase/db/db.html)
* [matplotlib](https://matplotlib.org/)
* [mp-api](https://pypi.org/project/mp-api/)
* numpy, pandas, spglib, scipy

## 🛠️ Getting Started

### Step 1: Set Up Environment

Create and activate a virtual environment:
```bash
# Create virtual environment
# Please make sure python version >= 3.10
python -m venv venv

# Activate the environment
source venv/bin/activate
```

### Step 2: Install AutoCatLab 

```bash
pip3 install git+https://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@github.com/ruchikamahajan66/autocatlab_v3.git 
```

Verify installation:
```bash
autocatlab --help
```
### Step 2.1: Install CatKit

```bash
pip3 install git+https://github.com/ruchikamahajan66/CatKit.git@fix_requirements#egg=CatKit 
```


Verify installation:
```bash
pip show CatKit
```

### Step 3: `Prepare` Configuration

Create a `config.json` file following the structure outlined in the [Configuration Guide](#configuration-guide) section below.

### Step 4: Execute Workflow

#### Run DFT calculations (relaxation + DOS):
```bash
autocatlab start-dft --config /path/to/your/config.json
```
#### Resume DFT calculations (relaxation + DOS):
```bash
autocatlab resume-dft --config  /path/to/your/config.json
```

#### Run ICOHP calculations:
```bash
autocatlab start-icohp --config /path/to/your/config.json
```
#### Resume ICOHP calculations:
```bash
autocatlab resume-icohp --config /path/to/your/config.json
```

### Step 5: Monitor Calculation Status

A SQLite database (`workflow.db`) is automatically generated in your output directory (`workflow_output` in `config.json`) when you run DFT or ICOHP calculations. You can query it to check the status of your jobs.

Access the database through the SQLite CLI:
```bash
sqlite3 workflow.db
```
View the schema of a table
``` 
sqlite3 workflow.db ".schema calc_status"

```

```

#### Example Queries:

```sql
-- ===========================
-- Workflow Overview Queries
-- ===========================

-- List all workflows and their statuses
SELECT calc_unique_name, status, start_time, end_time, success
FROM workflow_details;

-- Find all failed workflows and their error messages
SELECT calc_unique_name, error, end_time
FROM workflow_details
WHERE success = 0;

-- Get all batches under a specific workflow
-- Replace 'YOUR_WORKFLOW_NAME' with your workflow unique name
SELECT batch_id, calculation_type, status, start_time, end_time
FROM workflow_batch_details
WHERE workflow_unique_name = 'YOUR_WORKFLOW_NAME';

-- ===========================
-- Batch Execution Queries
-- ===========================

-- List all executions in a given batch (example: batch_id = 1)
SELECT material_name, calculation_name, status, success
FROM workflow_batch_executions
WHERE batch_id = 1;

-- Count successful executions per batch
SELECT batch_id,
       COUNT(*) AS total_executions,
       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS successful_executions
FROM workflow_batch_executions
GROUP BY batch_id;

-- Show all failed material-level executions
SELECT material_name, error, batch_id
FROM workflow_batch_executions
WHERE success = 0;

-- Get full hierarchy: workflow → batch → executions
-- Replace 'YOUR_WORKFLOW_NAME' with your workflow unique name
SELECT wd.calc_unique_name,
       wb.batch_id,
       we.execution_id,
       we.material_name,
       we.status
FROM workflow_details wd
JOIN workflow_batch_details wb ON wd.calc_unique_name = wb.workflow_unique_name
JOIN workflow_batch_executions we ON wb.batch_id = we.batch_id
WHERE wd.calc_unique_name = 'YOUR_WORKFLOW_NAME';

-- Get most recent successful workflow
SELECT calc_unique_name, end_time
FROM workflow_details
WHERE success = 1
ORDER BY end_time DESC
LIMIT 1;

-- ===========================
-- Calculation Counts
-- ===========================

-- Count completed BULK_DFT_RELAX calculations
SELECT COUNT(*) AS completed_relax_count
FROM workflow_batch_executions
WHERE calculation_name = 'BULK_DFT_RELAX' AND status = 'completed' AND success = 1;

-- Count completed BULK_DFT_DOS calculations
SELECT COUNT(*) AS completed_dos_count
FROM workflow_batch_executions
WHERE calculation_name = 'BULK_DFT_DOS' AND status = 'completed' AND success = 1;

-- Count completed BULK_ICOHP calculations
SELECT COUNT(*) AS completed_icohp_count
FROM workflow_batch_executions
WHERE calculation_name = 'BULK_ICOHP' AND status = 'completed' AND success = 1;

-- ===========================
-- Performance and Timing Queries
-- ===========================

-- Find BULK_ICOHP calculations completed in less than 5 minutes (300 seconds)
SELECT material_name, batch_id, start_time, end_time,
       (strftime('%s', end_time) - strftime('%s', start_time)) AS duration_seconds
FROM workflow_batch_executions
WHERE calculation_name = 'BULK_ICOHP'
  AND status = 'completed'
  AND success = 1
  AND duration_seconds < 300;

-- Check execution time for each BULK_DFT_RELAX calculation
SELECT material_name, batch_id, start_time, end_time,
       (strftime('%s', end_time) - strftime('%s', start_time)) AS execution_time_seconds
FROM workflow_batch_executions
WHERE calculation_name = 'BULK_DFT_RELAX'
  AND status = 'completed'
  AND success = 1
ORDER BY execution_time_seconds ASC;

-- Check execution time for each BULK_DFT_DOS calculation
SELECT material_name, batch_id, start_time, end_time,
       (strftime('%s', end_time) - strftime('%s', start_time)) AS execution_time_seconds
FROM workflow_batch_executions
WHERE calculation_name = 'BULK_DFT_DOS'
  AND status = 'completed'
  AND success = 1
ORDER BY execution_time_seconds ASC;

-- Check execution time for each BULK_ICOHP calculation
SELECT material_name, batch_id, start_time, end_time,
       (strftime('%s', end_time) - strftime('%s', start_time)) AS execution_time_seconds
FROM workflow_batch_executions
WHERE calculation_name = 'BULK_ICOHP'
  AND status = 'completed'
  AND success = 1
ORDER BY execution_time_seconds ASC;


```

## 📚 Key Features

### Materials Project Integration

### Materials Input Options


You can specify input materials in three different ways:

1. **From a local directory** - Provide the path to a directory containing material files:
   ```json
   {
     "input": {
       "type": "location",
       "value": "/path/to/materials/directory",
       "mp_api_key": "your_materials_project_api_key"
     }
   }
   ```

2. **Using Materials Project IDs** - Provide a list of MP material IDs:
   ```json
   {
     "input": {
       "type": "mp_ids",
       "value": ["mp-14333", "mp-3748"],
       "mp_api_key": "your_materials_project_api_key"
     }
   }
   ```

3. **Using ase db** -provide ase db location and code will generate the materials input based on ase atoms object:
   ```json
   {
     "input": {
       "type": "ase_db",
       "value": "/path/to/your/ase/db/ase.db",
       "mp_api_key": "your_materials_project_api_key"
     }
   }
   ```

## ⚙️ Prepare config.json 
#### Complete Configuration Example

```json
{
  "workflow_unique_name": "testing_v3_2",
  "workflow_input": {
    "type": "location",
    "value": "/path/to/your/input/dir/",
    "mp_api_key": "/your/mp/api/key"
  },
  "workflow_output_directory": "/path/to/your/output/dir/",
  "batch_size": 2,
  "workflow_steps": {
    "dft": {
      "calculations": [
        "BULK_DFT_RELAX",
        "BULK_DFT_DOS"
      ],
      "submission_detail": {
        "gpu_queue": "debug",
        "time": "00:30:00",
        "node": 1,
        "gpu": 4,
        "nTask": 4,
        "cpusPertask": 32
      },
      "scheduler": {
        "type": "slurm",
        "prepend_commands": [
          "#SBATCH -A m2997_g",
          "export OMP_NUM_THREADS=1",
          "export OMP_PLACES=threads",
          "export OMP_PROC_BIND=spread",
          "module load vasp/6.4.3-gpu",
          "export VASP_PP_PATH=/global/cfs/cdirs/m2997/vasp-psp/pseudo54",
          "export DB_OUTPUT_PATH=/global/cfs/cdirs/m2997/vasp-psp/pseudo54"
        ]
      }
    },
    "icohp": {
      "calculations": [
        "BULK_ICOHP"
      ],
      "submission_detail": {
        "cpu_queue": "debug",
        "cpu_time": "00:15:00",
        "cpu_node": 1
      },
      "scheduler": {
        "type": "slurm",
        "prepend_commands": [
          "#SBATCH -A m2997",
          "export OMP_NUM_THREADS=128",
          "export OMP_PLACES=threads",
          "export OMP_PROC_BIND=spread",
          "export VASP_PP_PATH=/global/cfs/cdirs/m2997/vasp-psp/pseudo54"
        ]
      }
    }
  },
  "user_luj_values": {
    "Sc": {
      "L": 2,
      "U": 1.00,
      "J": 0.0
    },
    "Fe": {
      "L": 2,
      "U": 5.00,
      "J": 0.1
    }
  },
  "workflow_step_parameters": {
    "BULK_DFT_RELAX": {
      "istart": 0,
      "setups": {
        "base": "recommended",
        "W": "_sv"
      },
      "encut": 600,
      "xc": "PBE",
      "gga": "PE",
      "npar": 1,
      "gamma": true,
      "ismear": 0,
      "inimix": 0,
      "amix": 0.1,
      "bmix": 0.00001,
      "amix_mag": 0.1,
      "bmix_mag": 0.00001,
      "nelm": 250,
      "sigma": 0.05,
      "algo": "normal",
      "ibrion": 2,
      "isif": 3,
      "ediffg": -0.02,
      "ediff": 0.00000001,
      "prec": "Normal",
      "nsw": 200,
      "lvtot": false,
      "ispin": 2,
      "ldau": true,
      "ldautype": 2,
      "laechg": true,
      "lreal": false,
      "lasph": true,
      "ldauprint": 2,
      "lmaxmix": 6,
      "lorbit": 11,
      "kpar": 4
    },
    "BULK_DFT_DOS": {
      "istart": 0,
      "setups": {
        "base": "recommended",
        "W": "_sv"
      },
      "encut": 600,
      "xc": "PBE",
      "gga": "PE",
      "gamma": true,
      "ismear": 0,
      "inimix": 0,
      "amix": 0.1,
      "bmix": 0.00001,
      "amix_mag": 0.1,
      "bmix_mag": 0.00001,
      "nelm": 250,
      "sigma": 0.05,
      "algo": "normal",
      "ibrion": 2,
      "isif": 3,
      "ediffg": -0.02,
      "ediff": 0.00000001,
      "prec": "Normal",
      "nsw": 200,
      "lvtot": false,
      "ispin": 2,
      "ldau": true,
      "ldautype": 2,
      "laechg": true,
      "lreal": false,
      "lasph": true,
      "ldauprint": 2,
      "lmaxmix": 6,
      "lorbit": 11,
      "kpar": 4,
      "npar": 1
    },
    "BULK_ICOHP": {
      "basisSet": "pbeVaspFit2015",
      "COHPStartEnergy": "-100",
      "COHPEndEnergy": "100",
      "DensityOfEnergy": ".TRUE.",
      "max_radii": "2.3"
    }
  }
}

```

## 📝 How to Cite

```bibtex
@article{mahajan2024predicting,
  title = {AutoCatlab: Automated DFT+ICOHP calculations for both BULK and SURFACES},
  author = {Ruchika Mahajan and Kirsten Winther},
  journal = {x.x.x},
  volume = {x.x},
  issue = {x},
  pages = {12345},
  numpages = {6},
  year = {2025},
  month = {July},
  publisher = {American Physical Society},
  doi = {10.x.x.x},
  url = {https://link.aps.org/doi/10.1103/xxx}
}
```

## 👥 Authors

This software was jointly developed by Dr. Ruchika Mahajan and Dr. Kirsten Winther, with Dr. Winther also providing guidance and oversight.
## 📄 License

AutoCatLab is released under the MIT License.
