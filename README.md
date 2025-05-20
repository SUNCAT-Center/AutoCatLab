# AutoCatLab

AutoCatLab is a python library which seamlessly perform high-throughput calculations (e.g DFT and DFT+ICOHP ) along with all data analysis which is config Driven.
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
pip3 install git+https://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@github.com/ruchikamahajan66/autocatlab_v3.git```

Verify installation:
```bash
autocatlab --help
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
CREATE TABLE workflow_details (
	calc_unique_name VARCHAR(255) NOT NULL, 
	config_path VARCHAR(255) NOT NULL, 
	status VARCHAR(50), 
	start_time DATETIME NOT NULL, 
	end_time DATETIME, 
	success BOOLEAN, 
	error TEXT, 
	PRIMARY KEY (calc_unique_name)
);
CREATE TABLE workflow_batch_details (
	batch_id INTEGER NOT NULL, 
	workflow_unique_name VARCHAR(36) NOT NULL, 
	materials TEXT NOT NULL, 
	calculation_type TEXT NOT NULL, 
	result_batch_dir VARCHAR(255) NOT NULL, 
	script_path VARCHAR(255) NOT NULL, 
	job_id VARCHAR(255), 
	status VARCHAR(50), 
	start_time DATETIME NOT NULL, 
	end_time DATETIME, 
	success BOOLEAN, 
	error TEXT, 
	PRIMARY KEY (batch_id), 
	FOREIGN KEY(workflow_unique_name) REFERENCES workflow_details (calc_unique_name)
);
CREATE TABLE workflow_batch_executions (
	execution_id INTEGER NOT NULL, 
	workflow_unique_name VARCHAR(36) NOT NULL, 
	batch_id INTEGER NOT NULL, 
	material_name VARCHAR(255) NOT NULL, 
	result_material_dir VARCHAR(255) NOT NULL, 
	script_path VARCHAR(255) NOT NULL, 
	calculation_name VARCHAR(255) NOT NULL, 
	status VARCHAR(50), 
	start_time DATETIME NOT NULL, 
	end_time DATETIME, 
	success BOOLEAN, 
	error TEXT, 
	PRIMARY KEY (execution_id), 
	FOREIGN KEY(workflow_unique_name) REFERENCES workflow_details (calc_unique_name), 
	FOREIGN KEY(batch_id) REFERENCES workflow_batch_details (batch_id)
);

```

#### Example Queries:

```sql
-- Count completed DFT relax calculations
sqlite3 calculation.db "SELECT COUNT(*) FROM calc_status WHERE calc_unique_name = 'your_calculation_unique_name' AND calc_type = 'DFT_RELAX_EXECUTION' AND start_time != end_time;"

-- Count completed DOS calculations
sqlite3 calculation.db "SELECT COUNT(*) FROM calc_status WHERE calc_unique_name = 'your_calculation_unique_name' AND calc_type = 'DFT_DOS_EXECUTION' AND start_time != end_time;"

-- Count completed ICOHP calculations
sqlite3 calculation.db "SELECT COUNT(*) FROM calc_status WHERE calc_unique_name = 'your_calculation_unique_name' AND calc_type = 'ICOHP_EXECUTION' AND start_time != end_time;"

-- Find ICOHP calculations completed in less than 120 seconds
sqlite3 calculation.db "SELECT MATERIAL, SCRIPT_NAME FROM calc_status WHERE CALC_UNIQUE_NAME = 'your_calculation_unique_name' AND CALC_TYPE = 'ICOHP_EXECUTION' AND START_TIME != END_TIME AND (strftime('%s', END_TIME) - strftime('%s', START_TIME)) < 120;"

-- Check execution time for each ICOHP calculation
sqlite3 calculation.db "SELECT (strftime('%s', END_TIME) - strftime('%s', START_TIME)) AS duration, MATERIAL, SCRIPT_NAME FROM calc_status WHERE CALC_UNIQUE_NAME = 'demo_1' AND CALC_TYPE = 'ICOHP_EXECUTION' AND START_TIME != END_TIME;"
```

## 📚 Key Features

### Materials Project Integration

####  Download materials from [materials project](https://materialsproject.org/)
As name suggests, this functionality downloads the materials and its related information based upon filtter parameters. 
As an implementation, it uses ```.summary.search``` api of material library ```mp_api```.

| SN |        file        |                         description |
|----|:------------------:|------------------------------------:|
| 1  | ```database.py ``` |         download the materials data |

e.g. it calculates the mixed Iridium (Ir) oxides with other transition metals and exports its structure data (CIF format) in the directory called "cif_data". 


##  ICOHP ( Integrated Crystal Orbital Hamilton Population ) calculations
ICOHP calculation is done after the density of states (DOS) calculation. 
This method helps to understand the bonding properties of a material.

| SN |                        file/activity                        |                                                           description |
|----|:-----------------------------------------------------------:|----------------------------------------------------------------------:|
| 1  |                      ```submit.pbs ```                      |     job script for running ```vasp6``` on ```perlmutter GPU``` nodes. |
| 2  |                    ```lobster-4.1.0 ```                     |                  run  ```lobster-4.1.0```  with ```lobsterin``` file. |
| 3  |                   ```lobster_tools.py ```                   |  create lobster input and analyse the result of lobster calculations. |

## <a name="configuration-guide"></a>Configuration Guide

Your `config.json` file must include the following parameters:

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

3. **Using Materials Project custom query** - Use the MP API for custom filtering:
   ```json
   {
     "input": {
       "type": "mp_custom_query",
       "mp_api_key": "your_materials_project_api_key"
     }
   }
   ```

### Complete Configuration Example

```json
{
  "calc_unique_name": "my_calculation", 
   "calc_type": ["DFT_SUBMISSION","ICOHP_SUBMISSION"],
  "calc_steps": {
    "DFT_SUBMISSION": ["DFT_RELAX_EXECUTION", "DFT_DOS_EXECUTION"],
    "ICOHP_SUBMISSION": ["ICOHP_EXECUTION"]
  },
  "workflow_output": "/pscratch/sd/r/ruchika/calc_2025/calc/Kirsten_binary_W_calculation/output/",
  "input": {
    "type": "location",
    "value": "/pscratch/sd/r/ruchika/calc_2025/calc/Kirsten_binary_W_calculation/input/",
    "mp_api_key": "your mp api key"
  },
  "submission_detail": {
    "dft": {
      "batch" : 1,
      "gpu_queue": "debug",
      "time": "00:30:00",
      "node": 1,
      "gpu": 4
    },
    "icohp": {
      "batch" : 1,
      "cpu_queue": "debug",
      "cpu_time": "00:30:00",
      "cpu_node": 1
    }
  },
  "calculation_parameters": {
    "relax": {
      "istart": 0,
      "setups": "recommended",
      "encut": 520,
      "xc": "PBE",
      "gga": "PE",
      "gamma": true,
      "ismear": 0,
      "inimix": 0.25,
      "amix": 0.2,
      "bmix": 0.001,
      "amix_mag": 0.8,
      "bmix_mag": 0.001,
      "nelm": 100,
      "sigma": 0.05,
      "algo": "Normal",
      "ibrion": 2,
      "ediffg": -0.02,
      "ediff": 1e-5,
      "prec": "Accurate",
      "nsw": 200,
      "lvtot": false,
      "ispin": 2,
      "ldau": true,
      "ldautype": 2,
      "laechg": true,
      "lreal": "Auto",
      "lasph": true,
      "ldauprint": 1,
      "lmaxmix": 4,
      "lorbit": 11,
      "nedos": 2000
    }
  }
}
```

## 📝 How to Cite

```bibtex
@article{mahajan2024predicting,
  title = {Predicting the stability and catalytic activities of mixed transition metal oxides},
  author = {Ruchika Mahajan and Kirsten Winther},
  journal = {x.x.x},
  volume = {x.x},
  issue = {x},
  pages = {12345},
  numpages = {6},
  year = {2024},
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
