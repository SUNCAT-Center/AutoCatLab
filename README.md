# AutoCatLab

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ASE](https://img.shields.io/badge/ASE-compatible-green.svg)](https://wiki.fysik.dtu.dk/ase/)

**AutoCatLab** is a powerful Python library for seamless high-throughput computational (Density Functional Theory) DFT calculations. It performs automated DFT and DFT+ICOHP (Integrated Crystal Orbital Hamilton Population) calculations for both **bulk materials** and **surfaces** with comprehensive data analysis through a configuration-driven approach. 

## ✨ Key Features

- 🔬 **High-throughput DFT calculations** for bulk and surface systems
- 📊 **Automated ICOHP analysis** for chemical bonding insights  
- 🎯 **Config-driven workflows** - no complex scripting required
- 🔗 **Materials Project integration** for easy material discovery
- 📈 **Built-in progress tracking** with SQLite database
- 🖥️ **HPC cluster support** with SLURM scheduler integration
- 🔄 **Resume functionality** for interrupted calculations
- 🧮 **Surface generation** via CatKit integration

## 🚀 Quick Start

### Installation

```bash
# Create and activate virtual environment (Python 3.10+ required)
python -m venv autocatlab-env
source autocatlab-env/bin/activate  

# Install AutoCatLab
pip3 install git+https://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@github.com/SUNCAT-Center/AutoCatLab.git
# Install CatKit for surface generation
pip3 install git+https://github.com/ruchikamahajan66/CatKit.git@fix_requirements#egg=CatKit 

# Verify installation
autocatlab --help
pip show CatKit 
```

### Basic Usage

```bash
# Start DFT calculations
autocatlab start-dft --config /path/to/your/config.json

# Resume interrupted calculations  
autocatlab resume-dft --config /path/to/your/config.json

# Run ICOHP analysis
autocatlab start-icohp --config /path/to/your/config.json

# Resume ICOHP analysis
autocatlab resume-icohp --config /path/to/your/config.json

# Monitor progress
autocatlab show-progress --config /path/to/your/config.json
```

## 📋 Prerequisites

### Required Dependencies
- **[PyTorch](https://pytorch.org/)** - Deep learning framework
- **[scikit-learn](https://scikit-learn.org/)** - Machine learning library
- **[pymatgen](https://pymatgen.org/)** - Materials analysis
- **[ASE](https://wiki.fysik.dtu.dk/ase/)** & **[ASE DB](https://wiki.fysik.dtu.dk/ase/ase/db/db.html)** - Atomistic simulation environment
- **[matplotlib](https://matplotlib.org/)** - Plotting library
- **[mp-api](https://pypi.org/project/mp-api/)** - Materials Project API
- **Standard scientific libraries**: numpy, pandas, spglib, scipy

### External Software
- **VASP** - Vienna Ab initio Simulation Package (license required)
- **LOBSTER** - For ICOHP calculations

## ⚙️ Configuration

AutoCatLab uses JSON configuration files to define workflows. Here's a comprehensive example:

### Material Input Options

Choose one of three input methods:

#### 1. Local Directory
```json
{
  "workflow_input": {
    "type": "location",
    "value": "/path/to/materials/directory",
    "mp_api_key": "your_materials_project_api_key"
  }
}
```

#### 2. Materials Project IDs
```json
{
  "workflow_input": {
    "type": "mp_ids", 
    "value": "mp-14333, mp-3748",
    "mp_api_key": "your_materials_project_api_key"
  }
}
```

#### 3. ASE Database
```json
{
  "workflow_input": {
    "type": "ase_db",
    "value": "/path/to/ase.db",
    "mp_api_key": "your_materials_project_api_key"
  }
}
```

### Complete Configuration Example

<details>
<summary>Click to expand full config.json example</summary>

```json
{
  "workflow_unique_name": "workflow",
  "workflow_input": {
    "type": "mp_mpids",
    "value": "mp-996996, mp-2311, mp-2310",
    "mp_api_key": "your/mp/api/key"
  },
  "workflow_output_directory": "/output/path/",
  "batch_size": 1,
  "workflow_steps": {
    "dft": {
      "calculations": [
        "BULK_DFT_RELAX",
        "BULK_DFT_DOS"
      ],
      "submission_detail": {
        "gpu_queue": "regular",
        "time": "02:00:00",
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
        "cpu_queue": "regular",
        "cpu_time": "01:00:00",
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
      "istart": 1,
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
      "ediff": 0.00000001,
      "prec": "Normal",
      "nsw": 0,
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
      "isym" :0,
      "nedos":3000,
      "kpar": 4,
      "npar": 1
    },
    "BULK_ICOHP": {
      "basisSet": "pbeVaspFit2015",
      "COHPStartEnergy": "-40",
      "COHPEndEnergy": "40",
      "DensityOfEnergy": ".TRUE.",
      "max_radii": "3"
    }
  }
}
```
</details>

## 🔬 Supported Calculations

### Bulk Material Calculations
- **`BULK_DFT_RELAX`** - Structure optimization
- **`BULK_DFT_DOS`** - Density of states calculation  
- **`BULK_ICOHP`** - Chemical bonding analysis

### Surface Calculations  
- **`SURFACE_DFT_RELAX`** - Surface structure optimization
- **`SURFACE_DFT_DOS`** - Surface density of states
- **`SURFACE_ICOHP`** - Surface bonding analysis

### Combined Workflows
For comprehensive surface energy calculations:
```json
{"calculations": [
  "BULK_DFT_RELAX", "BULK_DFT_DOS", 
  "SURFACE_DFT_RELAX", "SURFACE_DFT_DOS"
]}
```

## 📊 Monitoring & Database Queries

A SQLite database (`workflow.db`) is automatically generated in your output directory (`workflow_output` in `config.json`) when you run DFT or ICOHP calculations. You can query it to check the status of your jobs.

### Command Line Monitoring
```bash
autocatlab show-progress --config config.json
```

### Database Queries

<details>
<summary>Click to expand useful SQL queries</summary>

```sql
-- View all workflow statuses
SELECT calc_unique_name, status, start_time, end_time, success
FROM workflow_details;

-- Find failed calculations
SELECT calc_unique_name, error, end_time  
FROM workflow_details
WHERE success = 0;

-- Count completed calculations by type
SELECT calculation_name, COUNT(*) as completed_count
FROM workflow_batch_executions  
WHERE status = 'completed' AND success = 1
GROUP BY calculation_name;

-- Check execution times
SELECT material_name, calculation_name,
       (strftime('%s', end_time) - strftime('%s', start_time)) AS duration_seconds
FROM workflow_batch_executions
WHERE status = 'completed' 
ORDER BY duration_seconds DESC;
```
</details>

## 🛠️ Advanced Usage

### Custom DFT Parameters
Modify `workflow_step_parameters` in your config file to customize VASP settings:

```json
{
  "BULK_DFT_RELAX": {
    "encut": 800,
    "kpar": 4,
    "npar": 1,
    "ismear": 0,
    "ldau": true,
    "ldautype": 2
  }
}
```

### HPC Integration
AutoCatLab supports SLURM job scheduling:

```json
{
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
}
```

## 🧪 Example Workflows

### 1. High-throughput Bulk Screening
```bash
# Screen 100+ materials for electronic properties
autocatlab start-dft --config bulk_screening.json
```

### 2. Surface Energy Calculations  
```bash
# Calculate surface energies for different Miller indices
autocatlab start-dft --config surface_energy.json
```

### 3. Chemical Bonding Analysis
```bash  
# Perform ICOHP analysis on relaxed structures
autocatlab start-icohp --config bonding_analysis.json
```

## 🐛 Troubleshooting

### Common Issues

**Installation Problems:**
```bash
# If pip install fails, try:
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir git+https://...
```

**VASP Errors:**
- Ensure `VASP_PP_PATH` is correctly set
- Check pseudopotential files are accessible
- Verify VASP module is loaded

**Memory Issues:**
- Reduce `batch_size` in configuration
- Adjust `kpar` and `npar` parameters
- Use appropriate queue resources

**Resume Functionality:**
```bash
# If calculations are interrupted:
autocatlab resume-dft --config config.json
```

## 📚 Documentation & Support

### Useful Links
- **[ASE Documentation](https://wiki.fysik.dtu.dk/ase/)** - Atomistic Simulation Environment
- **[VASP Manual](https://www.vasp.at/wiki/index.php/The_VASP_Manual)** - VASP documentation
- **[Materials Project](https://materialsproject.org/)** - Materials database
- **[LOBSTER](http://www.cohp.de/)** - ICOHP analysis tool

### Getting Help
- Check the [GitHub Issues](https://github.com/SUNCAT-Center/AutoCatLab/issues) for known problems
- Review configuration examples in the repository
- Ensure all dependencies are properly installed

## 📄 Citation

If you use AutoCatLab in your research, please cite:

```bibtex
@article{mahajan2025autocatlab,
  title = {AutoCatLab: An Automated High-Throughput Framework for Generating Electronic Descriptors for Catalysis},
  author = {Ruchika Mahajan and Kirsten Winther},
  journal = {Journal of xxxx-xxxx},
  volume = {XX},
  pages = {XXXX-XXXX},
  year = {2025},
  publisher = {Wiley},
  doi = {10.1002/jcc.XXXXX},
  url = {https://doi.org/10.xxx/jcc.XXXXX}
}
```

## 👥 SUNCAT-affiliated developers of AutoCatLab

<div align="center">

<table style="border: none;">
<tr style="border: none;">
<td align="center" style="border: none;">
<img src="https://github.com/ruchikamahajan66.png" width="150" height="150" style="border-radius: 50%;">
<br><br>
<strong><a href="https://suncat.stanford.edu/people/ruchika-mahajan"> Dr. Ruchika Mahajan</a></strong>
<br>
Lead Developer
<br><br>
Postdoctoral Scholar, SUNCAT, SLAC<br>National Accelerator Laboratory, Stanford University
</td>
<td align="center" style="border: none;">
<img src="https://github.com/kirstenwinther.png" width="150" height="150" style="border-radius: 50%;">
<br><br>
<strong><a href="https://suncat.stanford.edu/people/kirsten-winther">Dr. Kirsten Winther</a></strong>
<br>
Co-Developer & Scientific Advisor
<br><br>
Associate Staff Scientist, SUNCAT, SLAC<br>National Accelerator Laboratory
</td>
</tr>
</table>

</div>

## 📞 Contact

For questions, suggestions, or collaborations:
- **GitHub Issues**: [Report bugs or request features](https://github.com/SUNCAT-Center/AutoCatLab/issues)
- **Email**: Contact the development team through GitHub

- **Office Hours**: Join our weekly Zoom office hours  
  ⏰ **Every Friday from 2:00 – 3:00 PM (PST time)**  
  🔗 [Join Zoom Meeting](https://example.zoom.us/j/1234567890)  
  *(Feel free to drop in with questions about AutoCatLab!)*

## 📄 License

AutoCatLab is released under the [MIT License](LICENSE). See the LICENSE file for details.

---

<div align="center">

</div>