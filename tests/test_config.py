"""`pytest` tests for config.py."""
import pytest

import benchcab.config as bc
import benchcab.utils as bu


def test_read_config_pass():
    """Test read_config() passes as expected."""
    existent_path = bu.get_installed_root() / "data" / "test" / "config-valid.yml"

    # Test for a path that exists
    config = bc.read_config(existent_path)
    assert config


def test_read_config_fail():
    """Test that read_config() fails as expected."""
    nonexistent_path = bu.get_installed_root() / "data" / "test" / "config-missing.yml"

    # Test for a path that does not exist.
    with pytest.raises(FileNotFoundError):
        bc.read_config(nonexistent_path)


def test_validate_config_valid():
    """Test validate_config() for a valid config file."""
    valid_config = bu.load_package_data("test/config-valid.yml")
    assert bc.validate_config(valid_config)


def test_validate_config_invalid():
    """Test validate_config() for an invalid config file."""
    invalid_config = bu.load_package_data("test/config-invalid.yml")
    with pytest.raises(bc.ConfigValidationError):
        bc.validate_config(invalid_config)
