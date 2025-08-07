import json
import logging
from json import loads


class JsonReader:
    def __init__(self):
        """
        Assigning variables and Getting Logger
        """
        self.data = None

    def read_json_file(self, json_file):
        """
        Reading the Json file and returning the data

        :param json_file: Json File to Read
        :return: Returning the read Json Data
        """
        try:
            with open(json_file, 'r') as json_file_data:
                self.data = loads(json_file_data.read())
            logging.debug(f"Reading Json File - {json_file} and data is = " + str(self.data))
            return self.data
        except Exception as ex:
            logging.exception(f"Exception while reading the json file {json_file}")

    def write_json_file(self, json_file_path, json_file):
        """
        Writing the Json file

        :param json_file_path:
        :param json_file: Json File to write
        :return: None
        """
        try:
            with open(json_file_path, 'w') as json_file_data:
                json_file_data.write(json.dumps(json_file))
            logging.debug(f"Writing to file: {json_file_path}, Json: {json_file}")
        except Exception as err:
            logging.exception(f"Exception while writing to json file {json_file}")
