"""`pytest` tests for `workdir.py`.

Note: explicit teardown for generated files and directories are not required as
the working directory used for testing is cleaned up in the `_run_around_tests`
pytest autouse fixture.
"""

from pathlib import Path

import pytest

from benchcab import internal
from benchcab.workdir import (
    clean_realisation_files,
    clean_submission_files,
    setup_fluxsite_directory_tree,
    setup_spatial_directory_tree,
)


class TestSetupFluxsiteDirectoryTree:
    """Tests for `setup_fluxsite_directory_tree()`."""

    @pytest.fixture(autouse=True)
    def fluxsite_directory_list(self):
        """Return the list of work directories we want benchcab to create."""
        return [
            Path("runs", "fluxsite"),
            Path("runs", "fluxsite", "logs"),
            Path("runs", "fluxsite", "outputs"),
            Path("runs", "fluxsite", "tasks"),
            Path("runs", "fluxsite", "analysis"),
            Path("runs", "fluxsite", "analysis", "bitwise-comparisons"),
        ]

    def test_directory_structure_generated(self, fluxsite_directory_list):
        """Success case: generate the full fluxsite directory structure."""
        setup_fluxsite_directory_tree()
        for path in fluxsite_directory_list:
            assert path.exists()


class TestSetupSpatialDirectoryTree:
    """Tests for `setup_spatial_directory_tree()`."""

    @pytest.fixture()
    def spatial_directory_list(self):
        """Return the list of work directories we want benchcab to create."""
        return [
            Path("runs", "spatial"),
            Path("runs", "spatial", "tasks"),
            Path("runs", "payu-laboratory"),
        ]

    def test_directory_structure_generated(self, spatial_directory_list):
        """Success case: generate spatial directory structure."""
        setup_spatial_directory_tree()
        for path in spatial_directory_list:
            assert path.exists()


class TestCleanFiles:
    """Tests for `clean_directory_tree()` and `clean_cwd_logfiles)."""

    @pytest.fixture(autouse=True)
    def set_internal_cwd(self, monkeypatch):
        """Sets internal.CWD to pytest's working directory."""
        monkeypatch.setattr(internal, "CWD", Path.cwd())

    @pytest.fixture()
    def src_path(self) -> Path:
        return Path("src")

    @pytest.fixture()
    def runs_path(self) -> Path:
        return Path("runs")

    @pytest.fixture(params=["rev_number-0.log", "rev_number-200.log"])
    def revision_log_file(self, request) -> Path:
        return Path(request.param)

    @pytest.fixture(
        params=["benchmark_cable_qsub.sh.o21871", "benchmark_cable_qsub.sh"]
    )
    def pbs_job_file(self, request) -> Path:
        return Path(request.param)

    def test_clean_realisation_files(
        self, src_path: Path, tmp_path: Path, revision_log_file: Path
    ):
        """Success case: Realisation files created by benchcab are removed after clean."""
        src_path.mkdir()
        cable_symlink = src_path / "main"
        # tmp_path contains the path being symlinked
        local_cable_src_path = tmp_path / "CABLE"
        local_cable_src_path.mkdir()
        cable_symlink.symlink_to(local_cable_src_path)
        revision_log_file.touch()
        clean_realisation_files()

        assert local_cable_src_path.exists()
        assert not src_path.exists()
        assert not revision_log_file.exists()

    def test_clean_submission_files(self, runs_path, pbs_job_file):
        """Success case: Submission files created by benchcab are removed after clean."""
        runs_path.mkdir()
        pbs_job_file.touch()
        clean_submission_files()
        assert not runs_path.exists()
        assert not pbs_job_file.exists()
