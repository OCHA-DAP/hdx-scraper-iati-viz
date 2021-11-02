from os import listdir
from os.path import join

from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir
from iati.data import download_all, is_xml


class TestDownload:
    def test_download(self, configuration, fixtures_dir):
        with temp_dir(
            "TestIATIVizDownload", delete_on_success=True, delete_on_failure=False
        ) as tempdir:
            with Download(user_agent="test") as downloader:
                download_all(
                    configuration,
                    tempdir,
                    whattorun="covid",
                    dportal_params="LIMIT 10 OFFSET 10",
                    downloader=downloader,
                )
                assert sorted(listdir(tempdir)) == [
                    "currentrates.json",
                    "dportal_0.xml",
                    "rates.csv",
                ]
                path = join(tempdir, "dportal_0.xml")
                assert is_xml(path) is True

                download_all(
                    configuration,
                    tempdir,
                    whattorun="covid",
                    dportal_params="LIMIT 1 OFFSET 100000",
                    downloader=downloader,
                )
                assert sorted(listdir(tempdir)) == [
                    "currentrates.json",
                    "dportal_0.xml",
                    "rates.csv",
                ]
                assert is_xml(path) is False
