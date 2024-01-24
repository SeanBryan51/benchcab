"""`pytest` tests for config.py."""
from copy import deepcopy
from pprint import pformat

import pytest

import benchcab.config as bc
import benchcab.utils as bu

no_optional_config = {
    "project": "w97",
    "modules": ["intel-compiler/2021.1.1", "netcdf/4.7.4", "openmpi/4.1.0"],
    "realisations": [
        {"repo": {"svn": {"branch_path": "trunk"}}},
        {
            "repo": {"svn": {"branch_path": "branches/Users/ccc561/v3.0-YP-changes"}},
        },
    ],
}

all_optional_config = {
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
            "repo": {"svn": {"branch_path": "branches/Users/ccc561/v3.0-YP-changes"}},
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
                "cable_user": {"FWSOIL_SWITCH": "Haverd2013", "GS_SWITCH": "leuning"}
            }
        },
        {"cable": {"cable_user": {"FWSOIL_SWITCH": "standard", "GS_SWITCH": "medlyn"}}},
        {
            "cable": {
                "cable_user": {"FWSOIL_SWITCH": "standard", "GS_SWITCH": "leuning"}
            }
        },
    ],
}


def test_read_config_file_pass():
    """Test read_config() reads an existing file."""
    existent_path = bu.get_installed_root() / "data" / "test" / "config-valid.yml"

    # Test for a path that exists
    config = bc.read_config_file(existent_path)
    assert pformat(config) == pformat(no_optional_config)


def test_read_config_file_fail():
    """Test that read_config() does not work for a non-existent file."""
    nonexistent_path = bu.get_installed_root() / "data" / "test" / "config-missing.yml"

    # Test for a path that does not exist.
    with pytest.raises(FileNotFoundError):
        _ = bc.read_config_file(nonexistent_path)


def test_validate_config_valid():
    """Test validate_config() for a valid config file."""
    valid_config = bu.load_package_data("test/config-valid.yml")
    assert bc.validate_config(valid_config)


def test_validate_config_invalid():
    """Test validate_config() for an invalid config file."""
    invalid_config = bu.load_package_data("test/config-invalid.yml")
    with pytest.raises(bc.ConfigValidationError):
        bc.validate_config(invalid_config)


def test_read_optional_key_add_data():
    """Test default key-values are added if not provided by config.yaml."""
    # Config having no optional keys
    config = deepcopy(no_optional_config)
    bc.read_optional_key(config)
    assert pformat(config) == pformat(all_optional_config)


def test_read_optional_key_same_data():
    """Test optional key-values are unchanged if provided by config.yaml."""
    # Config having all optional keys
    config = deepcopy(all_optional_config)
    bc.read_optional_key(config)
    assert pformat(config) == pformat(all_optional_config)


def test_read_config():
    """Test overall behaviour of read_config."""
    expected_config = deepcopy(all_optional_config)
    path = bu.get_installed_root() / "data" / "test" / "config-valid.yml"
    assert pformat(bc.read_config(path)) == pformat(expected_config)
