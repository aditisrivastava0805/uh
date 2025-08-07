#!/usr/bin/python
# Copyright (c) 2019 Ericsson Inc
# All rights reserved.
# The Copyright to the computer program(s) herein is the property of Ericsson AB, Sweden.
# The program(s) may be used and/or copied with the written permission from Ericsson AB
# or in accordance with the terms and conditions stipulated in the agreement/contract
# under which the program(s) have been supplied.
#
#
# Fetches multiple KPI parameters and formats/outputs to a timestamped AIR_KPI file for kafka input
# No input parameters are needed for this execution
#
#       Author(s) : Ankit Kumar jain
#          Created : 2023-03-14
#
#     Version history:
#
# 1.2     2019-07-12 create a 2nd file for Kafka message creation
# 1.2     2019-05-30 CIP/DCIP updates
# 1.1     2019-05-17 path updates
# 1.0     2019-05-07 First version
#
import logging
import os
import sys
from typing import List

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from KPI_Helper import files_newer_that_mins
from SubprocessClass import SubprocessClass

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


import lxml.etree as ET


class KPI_SUCCESS:
    def __init__(self, script_dir, execution_period_mins, pm_files_local_dir: str):
        self.pm_files_local_dir = pm_files_local_dir
        self.execution_period_mins = execution_period_mins

        # Creating an object from subprocess class
        self.subprocess_obj = SubprocessClass()
        self.script_dir = script_dir
        self.pm_bulk_port = 22
        self.pm_bulk_name = None
        self.internal_ip = None
        self.pm_csv_file = os.path.join(script_dir, "pm_file.csv")
        self.measCollec_xsl = os.path.join(script_dir, "measCollec.xsl")

    def aggregate_pm_files_into_csv_file(self, pm_file_paths: List[str]):
        try:
            if os.path.exists(self.pm_csv_file):
                os.remove(self.pm_csv_file)

            logging.info(f"Aggregating {len(pm_file_paths)} PM files into file: {self.pm_csv_file} <- {pm_file_paths}")

            with open(self.pm_csv_file, "a") as fd:
                for pm_file_path in pm_file_paths:
                    dom = ET.parse(pm_file_path)
                    xslt = ET.parse(self.measCollec_xsl)
                    transform = ET.XSLT(xslt)
                    new_dom = transform(dom)
                    print(new_dom, file=fd)
        except Exception as err:
            logging.exception(f"Failed aggregating PM file into csv file ::: {str(err)}")
            return None

    def get_value_from_csv_file(self, cmd, error_codes_list=[]):
        try:
            kpi_val = 0
            out, error = self.subprocess_obj.execute_cmd(cmd)
            if out is not None:
                for line in out.splitlines():
                    logging.info(f"get_value_from_csv_file Line: {str(line)}")
                    value, stat = self.retrieve_kpi_value(line, error_codes_list=error_codes_list)
                    kpi_val = kpi_val + int(value)
                    logging.info(f"get_value_from_csv_file value: {str(kpi_val)}")
                return kpi_val, True
            return kpi_val, False
        except Exception as err:
            logging.error(f"Exception in get_value_from_csv_file ::: {str(err)}")

    @staticmethod
    def success_rate(total_req, error_req):
        try:
            return 0 if total_req == 0 else ((total_req - error_req) / total_req) * 100
        except Exception as err:
            logging.error(f"Exception in success_rate ::: {str(err)}")

    def grep_values_from_file(self, pm_file, counter_name, filters, error_codes_list=[]):
        try:
            stat = False
            locked = False
            request_data = 0
            if filters:
                for req in filters:
                    cmd = f"""grep countername={str(counter_name)} {pm_file} | grep {str(req)} """
                    logging.info(f"cmd ::: {str(cmd)}")
                    val, stat = self.get_value_from_csv_file(cmd, error_codes_list=error_codes_list)
                    if stat:
                        locked = True
                    request_data = request_data + int(val)
            else:
                cmd = f"""grep countername={str(counter_name)} {pm_file} """
                logging.info(f"cmd ::: {str(cmd)}")
                val, stat = self.get_value_from_csv_file(cmd, error_codes_list=error_codes_list)
                if stat:
                    locked = True
                request_data = request_data + int(val)
            return request_data, locked
        except Exception as err:
            logging.error(f"Exception in grep_data_from_file ::: {str(err)}")

    @staticmethod
    def retrieve_kpi_value(line, error_codes_list=[]):
        fields = line.split(",")
        if error_codes_list:
            for field in fields:
                if "response-code" in field:
                    res_code_val = field.split("=")
                    if res_code_val[1] in error_codes_list:
                        return 0, True

        for field in fields:
            if "countervalue" in field:
                key_value = field.split("=")
                kpi = ""
                if len(key_value) == 2:
                    kpi = key_value[1]

                return int(kpi), True
        return 0, False

    @staticmethod
    def retrieve_kpi(line):
        try:
            kpi = ""
            for field in line.split(","):
                if "countervalue" in field:
                    key_value = field.split("=")
                    kpi = ""
                    if len(key_value) == 2:
                        kpi = key_value[1]
                    return kpi, True
            return kpi, False
        except Exception as e:
            logging.error("Exception in write_kpi ::: " + str(e))

    def main(self, success_kpi_config):
        cmd: str = ""
        kpi_list = []

        # Taking path for last 3 updated files
        file_paths = files_newer_that_mins(self.pm_files_local_dir, "*.xml", self.execution_period_mins)

        # Reading Files and creating a self.pm_csv_file
        self.aggregate_pm_files_into_csv_file(file_paths)

        # SUCCESS_KPIs
        try:
            config_values = success_kpi_config
            for k, v in config_values.items():
                total_request = 0
                error_request = 0
                filters = []
                error_codes = []
                if "filters" in config_values[k].keys():
                    filters = str(config_values[k]["filters"]).split("|")
                    logging.info(f"Filters ::: {str(filters)}")

                if "code" in config_values[k].keys():
                    error_codes = str(config_values[k]["code"]).split("|")
                    logging.info(f"code ::: {str(error_codes)}")

                # For Total Traffic Request
                total_request, total_status = self.grep_values_from_file(self.pm_csv_file, config_values[k]['kpi_total'], filters)
                logging.info(f"{str(k)}_total: {str(total_request)}")

                # For Error Traffic Request
                error_request, error_status = self.grep_values_from_file(self.pm_csv_file, config_values[k]['kpi_error'], filters, error_codes_list=error_codes)
                logging.info(f"{str(k)}_error: {str(error_request)}")

                # Success Rate
                counter = self.success_rate(total_request, error_request)
                logging.info(f"{str(k)}_success rate: {str(counter)}")

                if config_values[k]["kpi"] == "SCAPV2_SESSIONS_SUCCESSFUL_RATE":
                    print(f"total_status: {str(total_status)}   :::: error_status: {str(error_status)}")
                    if total_status or error_status:
                        kpi_list.append(f"{str(config_values[k]['kpi']).upper()},{str(counter)}")
                else:
                    kpi_list.append(f"{str(config_values[k]['kpi']).upper()},{str(counter)}")
        except Exception as err:
            logging.error(f"Exception in SUCCESS Counter:: {str(err)}")
            return kpi_list
        return kpi_list


