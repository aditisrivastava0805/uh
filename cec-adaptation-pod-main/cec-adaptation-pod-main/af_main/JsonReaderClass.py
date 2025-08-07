from json import loads
import logging


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
            logging.info(f"Reading Json File - {json_file} and data is = " + str(self.data))
            return self.data
        except Exception as ex:
            logging.exception(f"Exception while reading the json file {json_file} ::: " + str(ex))