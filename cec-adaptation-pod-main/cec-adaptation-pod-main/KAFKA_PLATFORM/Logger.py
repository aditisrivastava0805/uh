import logging
import os
from datetime import date


class LoggingHandler:
    def __init__(self, script_dir):
        """
        Running logger configuration
        """
        path = os.path.join(script_dir, 'log')
        logging.basicConfig(level=logging.INFO, filename=f'{path}/kafka_platform_log_{date.today().strftime("%Y-%m-%d")}.log', filemode='a',
                            format='%(asctime)s - %(name)s - %('
                                   'levelname)s - %(message)s',
                            datefmt='%d/%m/%Y %H:%M:%S')

    @staticmethod
    def get_logger(name):
        """
        Returning the Logger

        :param name: Class Name
        :return: Returning Logger Object
        """
        return logging.getLogger(name)

