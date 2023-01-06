import dataiku
from dataiku.runnables import Runnable, ResultTable
from googlesheets_common import DSSConstants, extract_credentials, get_unique_slugs
from googlesheets import GoogleSheetsSession


class GoogleSheetsToDatasetsImporter(Runnable):
    """The base interface for a Python runnable"""

    def __init__(self, project_key, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config
        self.doc_id = self.config.get("doc_id")
        self.tabs_ids = self.config.get("tabs_ids")
        self.result_format = self.config.get("result_format")
        self.write_format = self.config.get("write_format")
        credentials, credentials_type = extract_credentials(config)
        self.session = GoogleSheetsSession(credentials, credentials_type)
        dss_client = dataiku.api_client()
        self.project = dss_client.get_project(project_key)
        self.project_datasets = list_project_datasets_names(self.project)

    def get_progress_target(self):
        """
        If the runnable will return some progress info, have this function return a tuple of 
        (target, unit) where unit is one of: SIZE, FILES, RECORDS, NONE
        """
        return None

    def run(self, progress_callback):
        """
        Do stuff here. Can return a string or raise an exception.
        The progress_callback is a function expecting 1 value: current progress
        """
        worksheets = self.session.get_spreadsheets(self.doc_id)
        spreadsheet_title = self.session.get_spreadsheet_title(self.doc_id)
        if not spreadsheet_title:
            spreadsheet_title = "Nameless spreadsheet"
        project_flow = self.project.get_flow()

        target_zone = get_zone_from_name(project_flow, spreadsheet_title)
        if not target_zone:
            target_zone = project_flow.create_zone(spreadsheet_title)

        result_table = ResultTable()
        result_table.add_column("actions", "Actions", "STRING")
        worksheets_titles = []
        for worksheet in worksheets:
            worksheet_title = worksheet.title
            worksheets_titles.append("{}_{}".format(spreadsheet_title, worksheet_title))
            worksheets_titles = get_unique_slugs(worksheets_titles)
            unique_worksheet_title = worksheets_titles[-1:][0]

            if worksheet_title in self.tabs_ids:
                rows = worksheet.get_all_values()
                dataset_title = unique_worksheet_title
                if dataset_title in self.project_datasets:
                    dataset = self.project.get_dataset(dataset_title)
                else:
                    params = {
                        "connection": "filesystem_folders",
                        "path": "{}/{}".format(self.project_key, dataset_title)
                    }
                    dataset = self.project.create_dataset(
                        dataset_title, "Filesystem", params=params, formatType='csv',
                        formatParams=DSSConstants.DEFAULT_DATASET_FORMAT
                    )
                    if target_zone:
                        dataset.move_to_zone(target_zone)
                set_dataset_as_managed(dataset)
                result_table.add_record(["Adding dataset {} to the flow".format(dataset_title)])
                output_dataset = dataiku.Dataset(dataset_title)
                column_names = rows[0]
                schema = []
                for column_name in column_names:
                    schema.append({"name": column_name, "type": "string"})
                output_dataset.write_schema(schema)
                data_rows = rows[1:]
                with output_dataset.get_writer() as writer:
                    for row in data_rows:
                        writer.write_row_array(row)

        return result_table


def list_project_datasets_names(project):
    project_datasets = []
    datasets = project.list_datasets()
    for dataset in datasets:
        dataset_name = dataset.get("name")
        project_datasets.append(dataset_name)
    return project_datasets


def get_zone_from_name(project_flow, zone_title):
    zones = project_flow.list_zones()
    for zone in zones:
        if zone.name == zone_title:
            return zone.id
    return None


def set_dataset_as_managed(dataset):
    dataset_definition = dataset.get_definition()
    dataset_definition["managed"] = True
    dataset.set_definition(dataset_definition)
