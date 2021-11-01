import filecmp
from os.path import join

from hdx.utilities.compare import assert_files_same
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve

from iati.main import start


class TestIATI:
    def test_run(self, configuration, fixtures_dir):
        with temp_dir(
            "TestIATIViz", delete_on_success=True, delete_on_failure=False
        ) as tempdir:
            with Download(user_agent="test") as downloader:
                today = "2021-05-06"
                start(
                    configuration,
                    today,
                    tempdir,
                    fixtures_dir,
                    whattorun="covid",
                    filterdate="2020-01",
                    downloader=downloader,
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
