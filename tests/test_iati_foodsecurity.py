import filecmp
from os.path import join

import pytest
from hdx.api.configuration import Configuration
from hdx.api.locations import Locations
from hdx.utilities.compare import assert_files_same
from hdx.utilities.downloader import Download
from hdx.utilities.errors_onexit import ErrorsOnExit
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve

from iati.lookups import Lookups
from iati.main import start


class TestIATIFoodSecurity:
    @pytest.fixture(scope="function")
    def configuration(self):
        Configuration._create(
            hdx_read_only=True,
            hdx_site="prod",
            user_agent="test",
            project_config_yaml=join("tests", "config", "project_configuration.yml"),
        )
        Locations.set_validlocations(
            [
                {"name": "afg", "title": "Afghanistan"},
                {"name": "pse", "title": "State of Palestine"},
            ]
        )
        return Configuration.read()

    @pytest.fixture(scope="class")
    def fixtures_dir(self):
        return join("tests", "fixtures", "foodsecurity")

    @pytest.fixture(scope="class")
    def input_dir(self, fixtures_dir):
        return join(fixtures_dir, "input")

    def test_run(self, configuration, fixtures_dir, input_dir):
        with ErrorsOnExit() as errors_on_exit:
            with temp_dir(
                "TestIATIFoodSecurity", delete_on_success=True, delete_on_failure=False
            ) as tempdir:
                with Download(user_agent="test") as downloader:
                    retriever = Retrieve(
                        downloader,
                        tempdir,
                        input_dir,
                        tempdir,
                        save=False,
                        use_saved=True,
                    )
                    today = "2022-12-05"
                    Lookups.clear()
                    start(
                        configuration,
                        today,
                        retriever,
                        tempdir,
                        dportal_params=None,
                        whattorun="foodsecurity",
                        startdate="2021-01-01",
                        saveprefiltered=False,
                        errors_on_exit=errors_on_exit,
                    )
                    for filename in ("flows", "transactions", "reporting_orgs"):
                        csv_filename = f"{filename}.csv"
                        expected_file = join(fixtures_dir, csv_filename)
                        actual_file = join(tempdir, csv_filename)
                        assert_files_same(expected_file, actual_file)
                        json_filename = f"{filename}.json"
                        expected_file = join(fixtures_dir, json_filename)
                        actual_file = join(tempdir, json_filename)
                        assert filecmp.cmp(expected_file, actual_file)
