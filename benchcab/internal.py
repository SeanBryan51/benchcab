"""internal.py: define all runtime constants in a single file."""

import os
from pathlib import Path


_, NODENAME, _, _, _ = os.uname()

CONFIG_REQUIRED_KEYS = ["realisations", "project", "modules", "experiment"]

# Parameters for job script:
QSUB_FNAME = "benchmark_cable_qsub.sh"
NCPUS = 18
MEM = "30GB"
WALL_TIME = "6:00:00"
MPI = False
MULTIPROCESS = True

# DIRECTORY PATHS/STRUCTURE:

# Path to the user's current working directory
CWD = Path.cwd()

# Path to the user's home directory
HOME_DIR = Path(os.environ["HOME"])

# Relative path to directory containing CABLE source codes
SRC_DIR = Path("src")

# Relative path to run directory that stores CABLE runs
RUN_DIR = Path("runs")

# Relative path to core namelist files
NAMELIST_DIR = Path("namelists")

# Relative path to CABLE Auxiliary repository
CABLE_AUX_DIR = SRC_DIR / "CABLE-AUX"

# Relative URL path to CABLE Auxiliary repository on SVN
CABLE_AUX_RELATIVE_SVN_PATH = "branches/Share/CABLE-AUX"

# TODO(Sean): hard coding paths assets in CABLE_AUX is brittle, these should
# be promoted to config parameters, especially since we no longer throw exceptions
# when the assets cannot be found.

# Relative path to CABLE grid info file
GRID_FILE = CABLE_AUX_DIR / "offline" / "gridinfo_CSIRO_1x1.nc"

# Relative path to modis_phenology_csiro.txt
PHEN_FILE = CABLE_AUX_DIR / "core" / "biogeochem" / "modis_phenology_csiro.txt"

# Relative path to pftlookup_csiro_v16_17tiles.csv
CNPBIOME_FILE = (
    CABLE_AUX_DIR / "core" / "biogeochem" / "pftlookup_csiro_v16_17tiles.csv"
)

# Relative path to root directory for CABLE site runs
SITE_RUN_DIR = RUN_DIR / "site"

# Relative path to directory that stores CABLE log files
SITE_LOG_DIR = SITE_RUN_DIR / "logs"

# Relative path to directory that stores CABLE output files
SITE_OUTPUT_DIR = SITE_RUN_DIR / "outputs"

# Relative path to tasks directory where cable executables are run from
SITE_TASKS_DIR = SITE_RUN_DIR / "tasks"

# Relative path to directory that stores results of analysis on model output
SITE_ANALYSIS_DIR = SITE_RUN_DIR / "analysis"

# Relative path to directory that stores bitwise comparison results
SITE_BITWISE_CMP_DIR = SITE_ANALYSIS_DIR / "bitwise-comparisons"

# Path to met files:
MET_DIR = Path("/g/data/ks32/CLEX_Data/PLUMBER2/v1-0/Met/")

# CABLE SVN root url:
CABLE_SVN_ROOT = "https://trac.nci.org.au/svn/cable"

# CABLE executable file name:
CABLE_EXE = "cable-mpi" if MPI else "cable"

# CABLE namelist file name:
CABLE_NML = "cable.nml"

# CABLE vegetation namelist file:
CABLE_VEGETATION_NML = "pft_params.nml"

# CABLE soil namelist file:
CABLE_SOIL_NML = "cable_soilparm.nml"

# CABLE fixed C02 concentration
CABLE_FIXED_CO2_CONC = 400.0

# CABLE standard output filename
CABLE_STDOUT_FILENAME = "out.txt"

# Contains the default science configurations used to run the CABLE test suite
# (when a science config file is not provided by the user)
DEFAULT_SCIENCE_CONFIGURATIONS = [
    {
        "cable": {
            "cable_user": {
                "GS_SWITCH": "medlyn",
                "FWSOIL_SWITCH": "Haverd2013",
            }
        }
    },
    {
        "cable": {
            "cable_user": {
                "GS_SWITCH": "leuning",
                "FWSOIL_SWITCH": "Haverd2013",
            }
        }
    },
    {
        "cable": {
            "cable_user": {
                "GS_SWITCH": "medlyn",
                "FWSOIL_SWITCH": "standard",
            }
        }
    },
    {
        "cable": {
            "cable_user": {
                "GS_SWITCH": "leuning",
                "FWSOIL_SWITCH": "standard",
            }
        }
    },
]

# Contains the site ids for each met forcing file associated with an experiment
# on modelevaluation.org
MEORG_EXPERIMENTS = {
    # List of site ids associated with the 'Five site test'
    # experiment (workspace: NRI Land testing), see:
    # https://modelevaluation.org/experiment/display/xNZx2hSvn4PMKAa9R
    "five-site-test": [
        "AU-Tum",
        "AU-How",
        "FI-Hyy",
        "US-Var",
        "US-Whs",
    ],
    # List of site ids associated with the 'Forty two site test'
    # experiment (workspace: NRI Land testing), see:
    # https://modelevaluation.org/experiment/display/urTKSXEsojdvEPwdR
    "forty-two-site-test": [
        "AU-Tum",
        "AU-How",
        "AU-Cum",
        "AU-ASM",
        "AU-GWW",
        "AU-Ctr",
        "AU-Stp",
        "BR-Sa3",
        "CA-Qfo",
        "CH-Dav",
        "CN-Cha",
        "CN-Din",
        "DE-Geb",
        "DE-Gri",
        "DE-Hai",
        "DE-Tha",
        "DK-Sor",
        "FI-Hyy",
        "FR-Gri",
        "FR-Pue",
        "GF-Guy",
        "IT-Lav",
        "IT-MBo",
        "IT-Noe",
        "NL-Loo",
        "RU-Fyo",
        "US-Blo",
        "US-GLE",
        "US-Ha1",
        "US-Me2",
        "US-MMS",
        "US-Myb",
        "US-NR1",
        "US-PFa",
        "US-FPe",
        "US-SRM",
        "US-SRG",
        "US-Ton",
        "US-UMB",
        "US-Var",
        "US-Whs",
        "US-Wkg",
    ],
}

OPTIONAL_COMMANDS = ["fluxnet-bitwise-cmp"]


def get_met_sites(experiment: str) -> list[str]:
    """Get a list of met forcing file basenames specified by an experiment

    The `experiment` argument either specifies a key in `MEORG_EXPERIMENTS` or a site id
    within the five-site-test experiment.

    Assume all site ids map uniquely to a met file in MET_DIR.
    """

    if experiment in MEORG_EXPERIMENTS["five-site-test"]:
        # the user is specifying a single met site
        return [next(MET_DIR.glob(f"{experiment}*")).name]

    met_sites = [
        next(MET_DIR.glob(f"{site_id}*")).name
        for site_id in MEORG_EXPERIMENTS[experiment]
    ]

    return met_sites
