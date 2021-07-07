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

    def test_run(self, configuration, fixtures_dir):
        with temp_dir('TestIATIViz', delete_on_success=True, delete_on_failure=False) as tempdir:
            with Download(user_agent='test') as downloader:
                retriever = Retrieve(downloader, tempdir, fixtures_dir, tempdir, save=False, use_saved=True)
                configuration['outputs']['folder'] = tempdir
                today = '2021-05-06'
                start(configuration, today, retriever, dportal_params=None)
                for filename in ('flows', 'transactions', 'reporting_orgs'):
                    csv_filename = f'{filename}.csv'
                    expected_file = join(fixtures_dir, csv_filename)
                    actual_file = join(tempdir, csv_filename)
                    assert_files_same(expected_file, actual_file)
                    json_filename = f'{filename}.json'
                    expected_file = join(fixtures_dir, json_filename)
                    actual_file = join(tempdir, json_filename)
                    assert filecmp.cmp(expected_file, actual_file)

