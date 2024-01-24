"""`pytest` tests for config.py."""
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from pprint import pformat

import pytest

import benchcab.config as bc
import benchcab.utils as bu


@pytest.fixture()
def config_str(request) -> str:
    """Provide relative YAML path from data files."""
    return f"test/{request.param}"


@pytest.fixture()
def config_path(config_str: str) -> Path:
    """Provide absolute YAML Path object from data files."""
    return bu.get_installed_root() / "data" / config_str


@pytest.fixture()
def empty_config() -> dict:
    """Empty dict Configuration."""
    return {}


@pytest.fixture()
def no_optional_config() -> dict:
    """Config with no optional parameters."""
    return {
        "project": "w97",
        "modules": ["intel-compiler/2021.1.1", "netcdf/4.7.4", "openmpi/4.1.0"],
        "realisations": [
            {"repo": {"svn": {"branch_path": "trunk"}}},
            {
                "repo": {
                    "svn": {"branch_path": "branches/Users/ccc561/v3.0-YP-changes"}
                },
            },
        ],
    }


@pytest.fixture()
def all_optional_config() -> dict:
    """Config with all optional parameters."""
    return {
        "project": "w97",
        "fluxsite": {
            "experiment": "forty-two-site-test",
            "multiprocess": True,
            "pbs": {"ncpus": 18, "mem": "30GB", "walltime": "6:00:00", "storage": []},
        },
        "modules": ["intel-compiler/2021.1.1", "netcdf/4.7.4", "openmpi/4.1.0"],
        "realisations": [
            {"name": None, "repo": {"svn": {"branch_path": "trunk"}}},
            {
                "name": None,
                "repo": {
                    "svn": {"branch_path": "branches/Users/ccc561/v3.0-YP-changes"}
                },
            },
        ],
        "science_configurations": [
            {
                "cable": {
                    "cable_user": {"FWSOIL_SWITCH": "Haverd2013", "GS_SWITCH": "medlyn"}
                }
            },
            {
                "cable": {
                    "cable_user": {
                        "FWSOIL_SWITCH": "Haverd2013",
                        "GS_SWITCH": "leuning",
                    }
                }
            },
            {
                "cable": {
                    "cable_user": {"FWSOIL_SWITCH": "standard", "GS_SWITCH": "medlyn"}
                }
            },
            {
                "cable": {
                    "cable_user": {"FWSOIL_SWITCH": "standard", "GS_SWITCH": "leuning"}
                }
            },
        ],
    }


@pytest.mark.parametrize(
    ("config_str", "output_config", "pytest_error"),
    [
        ("config-valid.yml", "no_optional_config", does_not_raise()),
        ("config-missing.yml", "empty_config", pytest.raises(FileNotFoundError)),
    ],
    indirect=["config_str"],
)
def test_read_config_file(config_path, output_config, pytest_error, request):
    """Test read_config_file() for a file that may/may not exist."""
    with pytest_error:
        config = bc.read_config_file(config_path)
        assert pformat(config) == pformat(request.getfixturevalue(output_config))


@pytest.mark.parametrize(
    ("config_str", "pytest_error"),
    [
        ("config-valid.yml", does_not_raise()),
        ("config-invalid.yml", pytest.raises(bc.ConfigValidationError)),
    ],
    indirect=["config_str"],
)
def test_validate_config(config_str, pytest_error):
    """Test validate_config() for a valid/invalid config file."""
    with pytest_error:
        config = bu.load_package_data(config_str)
        assert bc.validate_config(config)


@pytest.mark.parametrize("input_config", ["no_optional_config", "all_optional_config"])
def test_read_optional_key_add_data(input_config, all_optional_config, request):
    """Test default key-values are added if not provided by config.yaml, and existing keys stay intact."""
    # Config having no optional keys
    config = request.getfixturevalue(input_config)
    bc.read_optional_key(config)
    assert pformat(config) == pformat(all_optional_config)


@pytest.mark.parametrize("config_str", ["config-valid.yml"], indirect=["config_str"])
def test_read_config(config_path, all_optional_config):
    """Test overall behaviour of read_config."""
    output_config = bc.read_config(config_path)
    assert pformat(output_config) == pformat(all_optional_config)
