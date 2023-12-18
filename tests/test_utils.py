"""Tests for utilities."""
import pytest
import benchcab.utils as bu


def test_get_installed_root():
    """Test get_installed_root()."""

    # Test it actually returns something. We should be able to mock this.
    assert bu.get_installed_root()


def test_load_package_data_pass():
    """Test load_package_data() passes as expected."""
    
    assert isinstance(bu.load_package_data('config-schema.yml'), dict)


def test_load_package_data_fail():
    """Test load_package_data() fails as expected."""
    
    with pytest.raises(FileNotFoundError):
        missing = bu.load_package_data('config-missing.yml')


def test_get_logger_singleton():
    """Test get_logger() returns a singleton object..."""
    logger1 = bu.get_logger(name='benchcab')
    logger2 = bu.get_logger(name='benchcab')

    assert logger1 is logger2