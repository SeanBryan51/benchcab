"""`pytest` tests for bench_config.py"""

import os
import pytest
import yaml

from tests.common import make_barebones_config, make_barbones_science_config
from benchcab.internal import MEORG_PLUMBER_MET_FILES
from benchcab.bench_config import check_config, read_config
from benchcab.bench_config import check_science_config, read_science_config, get_science_config_id


def test_check_config():
    """Tests for `check_config()`."""

    # Success case: test barebones config is valid
    config = make_barebones_config()
    check_config(config)

    # Success case: branch configuration with missing revision key
    config = make_barebones_config()
    config["realisations"][0].pop("revision")
    check_config(config)

    # Success case: branch configuration with missing met_subset key
    config = make_barebones_config()
    config.pop("met_subset")
    check_config(config)

    # Failure case: test config without project key raises an exception
    with pytest.raises(ValueError):
        config = make_barebones_config()
        config.pop("project")
        check_config(config)

    # Failure case: test config without user key raises an exception
    with pytest.raises(ValueError):
        config = make_barebones_config()
        config.pop("user")
        check_config(config)

    # Failure case: test config without realisations key raises an exception
    with pytest.raises(ValueError):
        config = make_barebones_config()
        config.pop("realisations")
        check_config(config)

    # Failure case: test config without modules key raises an exception
    with pytest.raises(ValueError):
        config = make_barebones_config()
        config.pop("modules")
        check_config(config)

    # Failure case: test config when realisations contains more than two keys
    with pytest.raises(ValueError):
        config = make_barebones_config()
        config["realisations"][2] = {
            "name": "my_new_branch",
            "revision": -1,
            "trunk": False,
            "share_branch": False,
        }
        check_config(config)

    # Failure case: test config when realisations contains less than two keys
    with pytest.raises(ValueError):
        config = make_barebones_config()
        config["realisations"].pop(1)
        check_config(config)

    # Failure case: 'name' key is missing in branch configuration
    with pytest.raises(ValueError):
        config = make_barebones_config()
        config["realisations"][1].pop("name")
        check_config(config)

    # Failure case: 'trunk' key is missing in branch configuration
    with pytest.raises(ValueError):
        config = make_barebones_config()
        config["realisations"][1].pop("trunk")
        check_config(config)

    # Failure case: 'share_branch' key is missing in branch configuration
    with pytest.raises(ValueError):
        config = make_barebones_config()
        config["realisations"][1].pop("share_branch")
        check_config(config)

    # Failure case: value of met_subset is not a subset of MEORG_PLUMBER_MET_FILES
    with pytest.raises(ValueError):
        config = make_barebones_config()
        config["met_subset"] = ["foo", "bar"]
        check_config(config)

    # Failure case: user key is not a string
    with pytest.raises(TypeError):
        config = make_barebones_config()
        config["user"] = 123
        check_config(config)

    # Failure case: project key is not a string
    with pytest.raises(TypeError):
        config = make_barebones_config()
        config["project"] = 123
        check_config(config)

    # Failure case: realisations key is not a dictionary
    with pytest.raises(TypeError):
        config = make_barebones_config()
        config["realisations"] = ["foo", "bar"]
        check_config(config)

    # Failure case: modules key is not a list
    with pytest.raises(TypeError):
        config = make_barebones_config()
        config["modules"] = "netcdf"
        check_config(config)

    # Failure case: met_subset key is not a list
    with pytest.raises(TypeError):
        config = make_barebones_config()
        config["met_subset"] = {}
        check_config(config)

    # Failure case: type of config["branch"]["revision"] is
    # not an integer
    with pytest.raises(TypeError):
        config = make_barebones_config()
        config["realisations"][1]["revision"] = "-1"
        check_config(config)

    # Failure case: type of config["branch"]["trunk"] is
    # not an boolean
    with pytest.raises(TypeError):
        config = make_barebones_config()
        config["realisations"][1]["trunk"] = 0
        check_config(config)

    # Failure case: type of config["branch"]["share_branch"] is
    # not a boolean
    with pytest.raises(TypeError):
        config = make_barebones_config()
        config["realisations"][1]["share_branch"] = "0"
        check_config(config)


def test_read_config():
    """Tests for `read_config()`."""

    # Success case: write config to file, then read config from file
    config = make_barebones_config()
    filename = "config-barebones.yaml"

    with open(filename, "w", encoding="utf-8") as file:
        yaml.dump(config, file)

    res = read_config(filename)
    os.remove(filename)
    assert config == res

    # Success case: a specified branch with a missing revision number
    # should return a config with the default revision number
    config = make_barebones_config()
    config["realisations"][0].pop("revision")
    filename = "config-barebones.yaml"

    with open(filename, "w", encoding="utf-8") as file:
        yaml.dump(config, file)

    res = read_config(filename)
    os.remove(filename)
    assert config != res
    assert res["realisations"][0]["revision"] == -1

    # Success case: config branch with missing key: met_subset
    # should return a config with met_subset = MEORG_PLUMBER_MET_FILES
    config = make_barebones_config()
    config.pop("met_subset")
    filename = "config-barebones.yaml"

    with open(filename, "w", encoding="utf-8") as file:
        yaml.dump(config, file)

    res = read_config(filename)
    os.remove(filename)
    assert config != res
    assert res["met_subset"] == MEORG_PLUMBER_MET_FILES

    # Success case: config branch with an empty met_subset
    # should return a config with met_subset = MEORG_PLUMBER_MET_FILES
    config = make_barebones_config()
    config["met_subset"] = []
    filename = "config-barebones.yaml"

    with open(filename, "w", encoding="utf-8") as file:
        yaml.dump(config, file)

    res = read_config(filename)
    os.remove(filename)
    assert config != res
    assert res["met_subset"] == MEORG_PLUMBER_MET_FILES


def test_check_science_config():
    """Tests for `check_science_config()`."""

    # Success case: test barebones science config is valid
    science_config = make_barbones_science_config()
    check_science_config(science_config)

    # Failure case: outer dictionary key with invalid naming convention
    with pytest.raises(ValueError):
        science_config = make_barbones_science_config()
        science_config["science1"] = {"some_setting": True}
        check_science_config(science_config)

    # Failure case: outer dictionary key with invalid naming convention
    with pytest.raises(ValueError):
        science_config = make_barbones_science_config()
        science_config["sci_0"] = {"some_setting": True}
        check_science_config(science_config)

    # Failure case: outer dictionary key with invalid naming convention
    with pytest.raises(ValueError):
        science_config = make_barbones_science_config()
        science_config["sci"] = {"some_setting": True}
        check_science_config(science_config)

    # Failure case: outer dictionary key with invalid naming convention
    with pytest.raises(ValueError):
        science_config = make_barbones_science_config()
        science_config["0"] = {"some_setting": True}
        check_science_config(science_config)

    # Failure case: science config settings are not specified by a dictionary
    with pytest.raises(TypeError):
        science_config = make_barbones_science_config()
        science_config["sci0"] = "some_setting = true"
        check_science_config(science_config)


def test_get_science_config_id():
    """Tests for `check_science_config()`."""

    # Success case: single digit id
    assert get_science_config_id("sci0") == "0"

    # Success case: multi digit id
    assert get_science_config_id("sci000") == "000"

    # Failure case: outer dictionary key with invalid naming convention
    with pytest.raises(ValueError):
        get_science_config_id("science1")

    # Failure case: outer dictionary key with invalid naming convention
    with pytest.raises(ValueError):
        get_science_config_id("sci_0")

    # Failure case: outer dictionary key with invalid naming convention
    with pytest.raises(ValueError):
        get_science_config_id("sci")

    # Failure case: outer dictionary key with invalid naming convention
    with pytest.raises(ValueError):
        get_science_config_id("0")


def test_read_science_config():
    """Tests for `read_science_config()`."""

    # Success case: write science config to file, then read science config from file
    science_config = make_barbones_science_config()
    filename = "science-config-barebones.yaml"

    with open(filename, "w", encoding="utf-8") as file:
        yaml.dump(science_config, file)

    res = read_science_config(filename)
    os.remove(filename)
    assert science_config == res
