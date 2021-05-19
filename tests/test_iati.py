import filecmp
from os.path import join

import pytest
from hdx.hdx_configuration import Configuration
from hdx.hdx_locations import Locations
from hdx.utilities.compare import assert_files_same
from hdx.utilities.downloader import Download
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve

from iati.main import start


class TestIATI:
    @pytest.fixture(scope='function')
    def configuration(self):
        Configuration._create(hdx_read_only=True, hdx_site='prod', user_agent='test',
                              project_config_yaml=join('tests', 'config', 'project_configuration.yml'))
        Locations.set_validlocations([{'name': 'afg', 'title': 'Afghanistan'}, {'name': 'pse', 'title': 'State of Palestine'}])
        return Configuration.read()

    @pytest.fixture(scope='class')
    def fixtures_dir(self):
        return join('tests', 'fixtures')

    @pytest.fixture(scope='class')
    def input_dir(self, fixtures_dir):
        return join(fixtures_dir, 'input')

    def test_run(self, configuration, fixtures_dir, input_dir):
        with temp_dir('TestIATIViz', delete_on_success=True, delete_on_failure=False) as tempdir:
            with Download(user_agent='test') as downloader:
                retriever = Retrieve(downloader, tempdir, fixtures_dir, tempdir, save=False, use_saved=True)
                configuration['outputs']['folder'] = tempdir
                this_month = '2021-05'
                start(configuration, this_month, retriever, dportal_params=None)
                filename = 'transactions.csv'
                expected_file = join(fixtures_dir, filename)
                actual_file = join(tempdir, filename)
                assert_files_same(expected_file, actual_file)
                filename = 'transactions.json'
                expected_file = join(fixtures_dir, filename)
                actual_file = join(tempdir, filename)
                assert filecmp.cmp(expected_file, actual_file)
                filename = 'flows.csv'
                expected_file = join(fixtures_dir, filename)
                actual_file = join(tempdir, filename)
                assert_files_same(expected_file, actual_file)
                filename = 'flows.json'
                expected_file = join(fixtures_dir, filename)
                actual_file = join(tempdir, filename)
                assert filecmp.cmp(expected_file, actual_file)

