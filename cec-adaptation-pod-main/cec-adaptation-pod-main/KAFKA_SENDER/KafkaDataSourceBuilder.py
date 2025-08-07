import json
from datetime import datetime

TABLE_KEY = "@table"

class DataSource:
    def __init__(self):
        self.message = dict()
        self.table = list()


class KafkaDataSourceBuilder:
    def __init__(self, message):
        self.ds = DataSource()
        self.set_message(message)

    def set_message(self, message):
        self.ds.message = message

    def set_message_field(self, key, value):
        self.ds.message[key] = value

    def add_data_record(self, data_items):
        self.ds.table.append(data_items)

    def data_source(self):
        return self.ds

    def write_to_file(self, file_path):
        self.write_to_json_file(file_path)
        self.write_to_tabular_file(file_path + '.csv')

    def write_to_json_file(self, file_path):
        document = {}
        document['message'] = self.ds.message
        table = [content[:-1] + ["NOT-SENT-TO-ONE-CONSOLE"] if len(content) > 3 else content for content in self.ds.table]
        document['table'] = table

        with open(file_path, 'w') as f:
            json.dump(document, f, indent=2)

    def write_to_tabular_file(self, file_path):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        m = self.ds.message

        with open(file_path, 'w') as f:
            for kpi_name, value, *_ in self.ds.table:
                f.write(m["config_item"] + ',' + kpi_name + ',' + value + ',' + timestamp + '\n')

# import json
# from datetime import datetime
# from typing import Any, Dict, List
#
# TABLE_KEY = "@table"
#
# class DataSource:
#     def __init__(self):
#         self.message: Dict[str, Any] = dict()
#         self.table: List[List[Any]] = list()
#
#
# class KafkaDataSourceBuilder:
#     def __init__(self, message: Dict[str, Any]):
#         self.ds : DataSource = DataSource()
#         self.set_message(message)
#
#     def set_message(self, message: Dict[str, Any]):
#         self.ds.message = message
#
#     def set_message_field(self, key: str, value: Any):
#         self.ds.message[key] = value
#
#     def add_data_record(self, data_items: List[Any]):
#         self.ds.table.append(data_items)
#
#     def data_source(self) -> DataSource:
#         return self.ds
#
#     def write_to_file(self, file_path: str):
#         self.write_to_json_file(file_path + '.json')
#         self.write_to_tabular_file(file_path)
#
#     def write_to_json_file(self, file_path: str):
#         document = {}
#         document['message'] = self.ds.message
#         document['table'] = self.ds.table
#         with open(file_path, 'w') as f:
#             json.dump(document, f, indent=2)
#
#     def write_to_tabular_file(self, file_path: str):
#         timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#
#         m = self.ds.message
#
#         with open(file_path, 'w') as f:
#             for kpi_name, value, _ in self.ds.table:
#                 f.write(f'{m["config_item"]},{kpi_name},{value},{timestamp}\n')
