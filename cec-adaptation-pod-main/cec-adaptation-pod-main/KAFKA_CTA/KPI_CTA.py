#!/usr/bin/sudo /usr/bin/python3
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
#          Created : 2022-04-19
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
import time
from datetime import datetime, timedelta
from typing import List
import pexpect

from KPI_Helper import banner, files_newer_that_mins
from SubprocessClass import SubprocessClass

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.kpi_csv_aggregator.aggregator import Aggregator, KpiAndValue, KpiDef, fs, Oper, CntType

from KAFKA_SENDER.KafkaDataSourceBuilder import KafkaDataSourceBuilder

import lxml.etree as ET
import gzip


class KPI_CTA:
    def __init__(self, script_dir, hostname, namespace, execution_period_mins, pm_files_local_dir: str,
                 is_test_mode: bool):
        self.is_test_mode = is_test_mode
        self.pm_files_local_dir = pm_files_local_dir
        self.yesterdayYMD = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')
        self.yesterdayYYMMDD = datetime.strftime(datetime.now() - timedelta(1), '%y-%m-%d')
        self.host_name = hostname
        self.namespace = namespace
        self.execution_period_mins = execution_period_mins
        self.currentDT = datetime.now()
        self.todayYMD = self.currentDT.strftime("%Y-%m-%d")
        self.todayYYMMDD = self.currentDT.strftime("%y-%m-%d")

        # Creating a object from subprocess class
        self.subprocess_obj = SubprocessClass()

        # epoch GMT time
        self.todayUTCMilli = int(time.mktime(self.currentDT.timetuple()) * 1000)

        if time.localtime().tm_isdst:
            self.timeDiff = time.timezone - 3600
        else:
            self.timeDiff = time.timezone

        self.localNowMilli = self.todayUTCMilli - self.timeDiff * 1000

        self.utcNow = datetime.utcnow()
        self.utcTimestamp = self.utcNow.strftime("%Y-%m-%d %H:%M:%S")
        self.todayUTC = self.utcNow.strftime("%Y-%m-%d")

        self.script_dir = script_dir
        self.pm_bulk_port = 22
        self.pm_bulk_name = None
        self.internal_ip = None
        self.GP = 300
        self.pm_csv_file = os.path.join(script_dir, f"{namespace}_pm_file.csv")
        self.measCollec_xsl = os.path.join(script_dir, "measCollec.xsl")

    @staticmethod
    def format_kpi_value(value: float) -> str:
        if type(value) == int or value.is_integer():
            return '{0:.0f}'.format(value)
        else:
            return '{0:.2f}'.format(round(value, 2))

    def add_kafka_kpi(self, kafka_data_source_builder: KafkaDataSourceBuilder, kpi: KpiAndValue):
        if kpi.value:
            value = kpi.value
            kpi_result = "UNDEFINED"
        else:
            value = 0
            kpi_result = "UNDEFINED"

        kafka_data_source_builder.add_data_record([kpi.name.upper(), self.format_kpi_value(value), kpi_result])

    def execute_kubectl(self, air, command, command_type=None):
        try:
            if "{" in command or "}" in command:
                command = command.replace("{", "{{")
                command = command.replace("}", "}}")
            if command_type == "bash":
                command = f"""kubectl exec -it {air} -- bash -c '{command}' """
            else:
                command = f"""kubectl exec -it -n {self.namespace} {air} -- {command} """
            logging.info(f"Command - {str(command)}")
            output, error = self.subprocess_obj.execute_cmd(command)
            return output, error
        except Exception as err:
            logging.error("Exception in update_command ::: " + str(err))

    @staticmethod
    def write_kpi(line):
        try:
            val = ""
            nf_instance = ""
            countername = ""
            envoy_response_code_class = ""
            instance = ""
            pool_name = ""
            nf_type = ""
            for field in line.split(","):
                if "countervalue" in field:
                    key_value = field.split("=")
                    if len(key_value) == 2:
                        val = key_value[1]

                if "nf_instance" in field:
                    nf_instance = field.split("=")
                    nf_instance = nf_instance[1]

                if "countername" in field:
                    countername = field.split("=")
                    countername = countername[1]

                if "envoy_response_code_class" in field:
                    envoy_response_code_class = field.split("=")
                    envoy_response_code_class = envoy_response_code_class[1]

                if ",instance" in field:
                    instance = field.split("=")
                    instance = instance[1]

                if "pool_name" in field:
                    pool_name = field.split("=")
                    pool_name = pool_name[1]

                if "nf_type" in field:
                    nf_type = field.split("=")
                    nf_type = nf_type[1]

            if envoy_response_code_class != "":
                if len(str(envoy_response_code_class)) == 1:
                    envoy_response_code_class = "0" + str(envoy_response_code_class)
                countername = str(countername).replace("xx", envoy_response_code_class)

            kpi_names = [str(nf_instance), str(nf_type), str(countername), str(pool_name), str(instance)]
            final_kpi_name = "_".join(i for i in kpi_names if i != "")
            return final_kpi_name, val
        except Exception as e:
            logging.error("Exception in write_kpi ::: " + str(e))

    def aggregate_pm_files_into_csv_file(self, pm_bulk, pm_file_paths: List[str]):
        try:
            if os.path.exists(self.pm_csv_file):
                os.remove(self.pm_csv_file)

            logging.info(f"Aggregating {len(pm_file_paths)} PM files into file: {self.pm_csv_file} <- {pm_file_paths}")

            with open(self.pm_csv_file, "a") as fd:
                for pm_file_path in pm_file_paths:
                    input_file_data = gzip.open(pm_file_path, 'r')
                    dom = ET.parse(input_file_data)
                    xslt = ET.parse(self.measCollec_xsl)
                    transform = ET.XSLT(xslt)
                    new_dom = transform(dom)
                    print(new_dom, file=fd)
        except Exception as err:
            logging.exception(f"Failed aggregating PM file into csv file {str(err)}")
            return None

    def write_pm_kpis(self, kafka_data_source_builder: KafkaDataSourceBuilder, interval_mins: int):
        logging.info(banner("Calculating KPIs"))

        # agg.values_by_kpi: OrderedDict[KpiDef, List[str]] = OrderedDict()

        agg = Aggregator(interval_mins)

        logging.info(f'Interval: {interval_mins} minutes')

        # DSCKPI_NUMBER_OF_TRAFFIC_TRANSACTIONS_PER_SECOND
        CC_IN_REQ_NUM_OF_MSGS_RECEIVED = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_NUM_OF_MSGS_RECEIVED",
                   fs(['countername=CC_IN_REQ_NUM_OF_MSGS_RECEIVED']), Oper.avg, CntType.Cnt))
        CC_REQ_NUM_OF_MSGS_PRODUCED = agg.reg_cnt(
            KpiDef(f"CC_REQ_NUM_OF_MSGS_PRODUCED",
                   fs(['countername=CC_REQ_NUM_OF_MSGS_PRODUCED']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_HX_BD_INITIALIZE = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_HX_BD_INITIALIZE",
                   fs(['countername=CC_IN_REQ_HX_BD_INITIALIZE']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_HX_BD_BINDING = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_HX_BD_BINDING",
                   fs(['countername=CC_IN_REQ_HX_BD_BINDING']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_HX_BD_VERIFY = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_HX_BD_VERIFY",
                   fs(['countername=CC_IN_REQ_HX_BD_VERIFY']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_HX_BD_TERM = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_HX_BD_TERM",
                   fs(['countername=CC_IN_REQ_HX_BD_TERM']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_HX_TR = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_HX_TR",
                   fs(['countername=CC_IN_REQ_HX_TR']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_HX_ERROR = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_HX_ERROR",
                   fs(['countername=CC_IN_REQ_HX_ERROR']), Oper.avg, CntType.Cnt))

        # DSCKPI_Traffic_Transaction_Success_Rate
        CC_OUT_ANS_NUM_OF_MSGS_SENT = agg.reg_cnt(
            KpiDef(f"CC_OUT_ANS_NUM_OF_MSGS_SENT",
                   fs(['countername=CC_OUT_ANS_NUM_OF_MSGS_SENT']), Oper.avg, CntType.Cnt))
        CC_ANS_NUM_OF_MSGS_CONSUMED = agg.reg_cnt(
            KpiDef(f"CC_ANS_NUM_OF_MSGS_CONSUMED",
                   fs(['countername=CC_ANS_NUM_OF_MSGS_CONSUMED']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_NUM_OF_MSGS_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_NUM_OF_MSGS_REJECTED",
                   fs(['countername=CC_IN_REQ_NUM_OF_MSGS_REJECTED']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_CAPACITY_LICENSE_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_CAPACITY_LICENSE_REJECTED",
                   fs(['countername=CC_IN_REQ_CAPACITY_LICENSE_REJECTED']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_THROTTLING_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_THROTTLING_REJECTED",
                   fs(['countername=CC_IN_REQ_THROTTLING_REJECTED']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_MISSING_AVP = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_MISSING_AVP",
                   fs(['countername=CC_IN_REQ_MISSING_AVP']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_INVALID_HDR_BITS = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_INVALID_HDR_BITS",
                   fs(['countername=CC_IN_REQ_INVALID_HDR_BITS']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_INVALID_AVP_BITS = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_INVALID_AVP_BITS",
                   fs(['countername=CC_IN_REQ_INVALID_AVP_BITS']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_FAILED_AVP_READ = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_FAILED_AVP_READ",
                   fs(['countername=CC_IN_REQ_FAILED_AVP_READ']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_APPLICATION_UNSUPPORTED = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_APPLICATION_UNSUPPORTED",
                   fs(['countername=CC_IN_REQ_APPLICATION_UNSUPPORTED']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_COMMAND_UNSUPPORTED = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_COMMAND_UNSUPPORTED",
                   fs(['countername=CC_IN_REQ_COMMAND_UNSUPPORTED']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_LOOP_DETECTED = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_LOOP_DETECTED",
                   fs(['countername=CC_IN_REQ_LOOP_DETECTED']), Oper.avg, CntType.Cnt))
        CC_INTERNAL_REASONS_NUM_OF_MSGS_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_INTERNAL_REASONS_NUM_OF_MSGS_REJECTED",
                   fs(['countername=CC_INTERNAL_REASONS_NUM_OF_MSGS_REJECTED']), Oper.avg, CntType.Cnt))
        CC_DMI_MS_NUM_OF_REQ_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_DMI_MS_NUM_OF_REQ_REJECTED",
                   fs(['countername=CC_DMI_MS_NUM_OF_REQ_REJECTED']), Oper.avg, CntType.Cnt))
        CC_DMI_SB_NUM_OF_REQ_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_DMI_SB_NUM_OF_REQ_REJECTED",
                   fs(['countername=CC_DMI_SB_NUM_OF_REQ_REJECTED']), Oper.avg, CntType.Cnt))
        CC_DMI_SB_NUM_OF_INIT_REJECTED_DB_LIMIT_REACHED = agg.reg_cnt(
            KpiDef(f"CC_DMI_SB_NUM_OF_INIT_REJECTED_DB_LIMIT_REACHED",
                   fs(['countername=CC_DMI_SB_NUM_OF_INIT_REJECTED_DB_LIMIT_REACHED']), Oper.avg, CntType.Cnt))
        CC_DMI_SB_NUM_OF_BIND_REJECTED_DB_LIMIT_REACHED = agg.reg_cnt(
            KpiDef(f"CC_DMI_SB_NUM_OF_BIND_REJECTED_DB_LIMIT_REACHED",
                   fs(['countername=CC_DMI_SB_NUM_OF_BIND_REJECTED_DB_LIMIT_REACHED']), Oper.avg, CntType.Cnt))
        CC_ROUTING_MSG_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_ROUTING_MSG_REJECTED",
                   fs(['countername=CC_ROUTING_MSG_REJECTED']), Oper.avg, CntType.Cnt))
        CC_MSG_SIZE_EXCEEDED_NUM_OF_REQ_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_MSG_SIZE_EXCEEDED_NUM_OF_REQ_REJECTED",
                   fs(['countername=CC_MSG_SIZE_EXCEEDED_NUM_OF_REQ_REJECTED']), Oper.avg, CntType.Cnt))
        CC_OUT_REQ_LOOP_PREVENTED = agg.reg_cnt(
            KpiDef(f"CC_OUT_REQ_LOOP_PREVENTED",
                   fs(['countername=CC_OUT_REQ_LOOP_PREVENTED']), Oper.avg, CntType.Cnt))
        CC_OUT_REQ_PEER_GROUP_LOOP_PREVENTED = agg.reg_cnt(
            KpiDef(f"CC_OUT_REQ_PEER_GROUP_LOOP_PREVENTED",
                   fs(['countername=CC_OUT_REQ_PEER_GROUP_LOOP_PREVENTED']), Oper.avg, CntType.Cnt))
        CC_OUT_REQ_TOO_BUSY = agg.reg_cnt(
            KpiDef(f"CC_OUT_REQ_TOO_BUSY",
                   fs(['countername=CC_OUT_REQ_TOO_BUSY']), Oper.avg, CntType.Cnt))
        CC_OUT_REQ_UNABLE_TO_DELIVER = agg.reg_cnt(
            KpiDef(f"CC_OUT_REQ_UNABLE_TO_DELIVER",
                   fs(['countername=CC_OUT_REQ_UNABLE_TO_DELIVER']), Oper.avg, CntType.Cnt))
        CC_OUT_REQ_PEER_GROUP_UNABLE_TO_DELIVER = agg.reg_cnt(
            KpiDef(f"CC_OUT_REQ_PEER_GROUP_UNABLE_TO_DELIVER",
                   fs(['countername=CC_OUT_REQ_PEER_GROUP_UNABLE_TO_DELIVER']), Oper.avg, CntType.Cnt))
        CC_OUT_REQ_NUM_OF_TRANSACTIONS_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_OUT_REQ_NUM_OF_TRANSACTIONS_REJECTED",
                   fs(['countername=CC_OUT_REQ_NUM_OF_TRANSACTIONS_REJECTED']), Oper.avg, CntType.Cnt))
        CC_OUT_REQ_THROTTLING_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_OUT_REQ_THROTTLING_REJECTED",
                   fs(['countername=CC_OUT_REQ_THROTTLING_REJECTED']), Oper.avg, CntType.Cnt))
        CC_OUT_REQ_DOIC_THROTTLING_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_OUT_REQ_DOIC_THROTTLING_REJECTED",
                   fs(['countername=CC_OUT_REQ_DOIC_THROTTLING_REJECTED']), Oper.avg, CntType.Cnt))
        CC_OUT_REQ_PEER_GROUP_THROTTLING_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_OUT_REQ_PEER_GROUP_THROTTLING_REJECTED",
                   fs(['countername=CC_OUT_REQ_PEER_GROUP_THROTTLING_REJECTED']), Oper.avg, CntType.Cnt))
        CC_OUT_REQ_PEER_GROUP_DOIC_THROTTLING_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_OUT_REQ_PEER_GROUP_DOIC_THROTTLING_REJECTED",
                   fs(['countername=CC_OUT_REQ_PEER_GROUP_DOIC_THROTTLING_REJECTED']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_ROAMING_PARTNER_ID_CHECKS_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_ROAMING_PARTNER_ID_CHECKS_REJECTED",
                   fs(['countername=CC_IN_REQ_ROAMING_PARTNER_ID_CHECKS_REJECTED']), Oper.avg, CntType.Cnt))
        CC_OUT_REQ_ROAMING_PARTNER_ID_CHECKS_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_OUT_REQ_ROAMING_PARTNER_ID_CHECKS_REJECTED",
                   fs(['countername=CC_OUT_REQ_ROAMING_PARTNER_ID_CHECKS_REJECTED']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_LOCAL_ID_CHECKS_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_LOCAL_ID_CHECKS_REJECTED",
                   fs(['countername=CC_IN_REQ_LOCAL_ID_CHECKS_REJECTED']), Oper.avg, CntType.Cnt))
        CC_OUT_ANS_HX_BD_INITIALIZE_SUCC = agg.reg_cnt(
            KpiDef(f"CC_OUT_ANS_HX_BD_INITIALIZE_SUCC",
                   fs(['countername=CC_OUT_ANS_HX_BD_INITIALIZE_SUCC']), Oper.avg, CntType.Cnt))
        CC_OUT_ANS_HX_BD_INITIALIZE_UNSUCC = agg.reg_cnt(
            KpiDef(f"CC_OUT_ANS_HX_BD_INITIALIZE_UNSUCC",
                   fs(['countername=CC_OUT_ANS_HX_BD_INITIALIZE_UNSUCC']), Oper.avg, CntType.Cnt))
        CC_OUT_ANS_HX_BD_BINDING_SUCC = agg.reg_cnt(
            KpiDef(f"CC_OUT_ANS_HX_BD_BINDING_SUCC",
                   fs(['countername=CC_OUT_ANS_HX_BD_BINDING_SUCC']), Oper.avg, CntType.Cnt))
        CC_OUT_ANS_HX_BD_BINDING_UNSUCC = agg.reg_cnt(
            KpiDef(f"CC_OUT_ANS_HX_BD_BINDING_UNSUCC",
                   fs(['countername=CC_OUT_ANS_HX_BD_BINDING_UNSUCC']), Oper.avg, CntType.Cnt))
        CC_OUT_ANS_HX_BD_VERIFY_SUCC = agg.reg_cnt(
            KpiDef(f"CC_OUT_ANS_HX_BD_VERIFY_SUCC",
                   fs(['countername=CC_OUT_ANS_HX_BD_VERIFY_SUCC']), Oper.avg, CntType.Cnt))
        CC_OUT_ANS_HX_BD_VERIFY_UNSUCC = agg.reg_cnt(
            KpiDef(f"CC_OUT_ANS_HX_BD_VERIFY_UNSUCC",
                   fs(['countername=CC_OUT_ANS_HX_BD_VERIFY_UNSUCC']), Oper.avg, CntType.Cnt))
        CC_OUT_ANS_HX_BD_TERMINATE_SUCC = agg.reg_cnt(
            KpiDef(f"CC_OUT_ANS_HX_BD_TERMINATE_SUCC",
                   fs(['countername=CC_OUT_ANS_HX_BD_TERMINATE_SUCC']), Oper.avg, CntType.Cnt))
        CC_OUT_ANS_HX_BD_TERMINATE_UNSUCC = agg.reg_cnt(
            KpiDef(f"CC_OUT_ANS_HX_BD_TERMINATE_UNSUCC",
                   fs(['countername=CC_OUT_ANS_HX_BD_TERMINATE_UNSUCC']), Oper.avg, CntType.Cnt))
        CC_OUT_ANS_HX_TR = agg.reg_cnt(
            KpiDef(f"CC_OUT_ANS_HX_TR",
                   fs(['countername=CC_OUT_ANS_HX_TR']), Oper.avg, CntType.Cnt))
        CC_OUT_ANS_HX_ERROR = agg.reg_cnt(
            KpiDef(f"CC_OUT_ANS_HX_ERROR",
                   fs(['countername=CC_OUT_ANS_HX_ERROR']), Oper.avg, CntType.Cnt))
        CC_NUM_OF_GENERATED_ANS_DROPPED = agg.reg_cnt(
            KpiDef(f"CC_NUM_OF_GENERATED_ANS_DROPPED",
                   fs(['countername=CC_NUM_OF_GENERATED_ANS_DROPPED']), Oper.avg, CntType.Cnt))
        CC_OUT_REQ_LOCAL_ID_CHECKS_REJECTED = agg.reg_cnt(
            KpiDef(f"CC_OUT_REQ_LOCAL_ID_CHECKS_REJECTED",
                   fs(['countername=CC_OUT_REQ_LOCAL_ID_CHECKS_REJECTED']), Oper.avg, CntType.Cnt))

        # PEERKPI_NUMBER_OF_TRANSACTIONS_PER_SECONDS_PER_PEER
        CC_IN_REQ_NUM_OF_MSGS_RECEIVED = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_NUM_OF_MSGS_RECEIVED",
                   fs(['countername=CC_IN_REQ_NUM_OF_MSGS_RECEIVED']), Oper.avg, CntType.Cnt))
        CC_OUT_REQ_NUM_OF_MSGS_SENT = agg.reg_cnt(
            KpiDef(f"CC_OUT_REQ_NUM_OF_MSGS_SENT",
                   fs(['countername=CC_OUT_REQ_NUM_OF_MSGS_SENT']), Oper.avg, CntType.Cnt))

        # PEERKPI_INCOMING_TRANSACTION_SUCCESS_RATE_PER_PEER
        CC_OUT_ANS_NUM_OF_MSGS_SENT = agg.reg_cnt(
            KpiDef(f"CC_OUT_ANS_NUM_OF_MSGS_SENT",
                   fs(['countername=CC_OUT_ANS_NUM_OF_MSGS_SENT']), Oper.avg, CntType.Cnt))
        CC_OUT_ANS_NUM_OF_MSGS_EBIT_SET = agg.reg_cnt(
            KpiDef(f"CC_OUT_ANS_NUM_OF_MSGS_EBIT_SET",
                   fs(['countername=CC_OUT_ANS_NUM_OF_MSGS_EBIT_SET']), Oper.avg, CntType.Cnt))
        CC_IN_REQ_NUM_OF_MSGS_RECEIVED = agg.reg_cnt(
            KpiDef(f"CC_IN_REQ_NUM_OF_MSGS_RECEIVED",
                   fs(['countername=CC_IN_REQ_NUM_OF_MSGS_RECEIVED']), Oper.avg, CntType.Cnt))


        # PEERKPI_OUTGOING_TRANSACTION_SUCCESS_RATE_PER_PEER
        CC_IN_ANS_NUM_OF_MSGS_RECEIVED = agg.reg_cnt(
            KpiDef(f"CC_IN_ANS_NUM_OF_MSGS_RECEIVED",
                   fs(['countername=CC_IN_ANS_NUM_OF_MSGS_RECEIVED']), Oper.avg, CntType.Cnt))
        CC_IN_ANS_NUM_OF_MSGS_EBIT_SET = agg.reg_cnt(
            KpiDef(f"CC_IN_ANS_NUM_OF_MSGS_EBIT_SET",
                   fs(['countername=CC_IN_ANS_NUM_OF_MSGS_EBIT_SET']), Oper.avg, CntType.Cnt))
        CC_OUT_REQ_NUM_OF_MSGS_SENT = agg.reg_cnt(
            KpiDef(f"CC_OUT_REQ_NUM_OF_MSGS_SENT",
                   fs(['countername=CC_OUT_REQ_NUM_OF_MSGS_SENT']), Oper.avg, CntType.Cnt))

        #
        # PARSE DATA FILE
        #
        agg.aggregate_counters(self.pm_csv_file)

        #
        # CALCULATE Simple KPIs and WRITE to Kafka file
        #
        print("agg.values_by_kpi  :::::::  ", agg.values_by_kpi)
        for kpi_def in agg.values_by_kpi.keys():
            if kpi_def.counter_type == CntType.KPI:
                self.add_kafka_kpi(kafka_data_source_builder, KpiAndValue(kpi_def.name, agg.calc_simple_kpi(kpi_def)))

        PEERKPI_NUMBER_OF_TRANSACTIONS_PER_SECONDS_PER_PEER = (agg.sum_counters(
            [CC_IN_REQ_NUM_OF_MSGS_RECEIVED, CC_OUT_REQ_NUM_OF_MSGS_SENT])) / self.GP

        DSCKPI_NUMBER_OF_TRAFFIC_TRANSACTIONS_PER_SECOND_partA = agg.sum_counters(
            [CC_IN_REQ_NUM_OF_MSGS_RECEIVED, CC_REQ_NUM_OF_MSGS_PRODUCED])
        DSCKPI_NUMBER_OF_TRAFFIC_TRANSACTIONS_PER_SECOND_partB = agg.sum_counters(
            [CC_IN_REQ_HX_BD_INITIALIZE, CC_IN_REQ_HX_BD_BINDING, CC_IN_REQ_HX_BD_VERIFY, CC_IN_REQ_HX_BD_TERM,
             CC_IN_REQ_HX_TR, CC_IN_REQ_HX_ERROR])
        DSCKPI_NUMBER_OF_TRAFFIC_TRANSACTIONS_PER_SECOND = (DSCKPI_NUMBER_OF_TRAFFIC_TRANSACTIONS_PER_SECOND_partA - DSCKPI_NUMBER_OF_TRAFFIC_TRANSACTIONS_PER_SECOND_partB) / self.GP

        partA = agg.sum_counters([CC_OUT_ANS_NUM_OF_MSGS_SENT, CC_ANS_NUM_OF_MSGS_CONSUMED])
        partB = agg.sum_counters(
            [CC_IN_REQ_NUM_OF_MSGS_REJECTED, CC_IN_REQ_CAPACITY_LICENSE_REJECTED, CC_IN_REQ_THROTTLING_REJECTED,
             CC_IN_REQ_MISSING_AVP, CC_IN_REQ_INVALID_HDR_BITS, CC_IN_REQ_INVALID_AVP_BITS, CC_IN_REQ_FAILED_AVP_READ,
             CC_IN_REQ_APPLICATION_UNSUPPORTED, CC_IN_REQ_COMMAND_UNSUPPORTED, CC_IN_REQ_LOOP_DETECTED,
             CC_INTERNAL_REASONS_NUM_OF_MSGS_REJECTED, CC_DMI_MS_NUM_OF_REQ_REJECTED, CC_DMI_SB_NUM_OF_REQ_REJECTED,
             CC_DMI_SB_NUM_OF_INIT_REJECTED_DB_LIMIT_REACHED, CC_DMI_SB_NUM_OF_BIND_REJECTED_DB_LIMIT_REACHED,
             CC_ROUTING_MSG_REJECTED, CC_MSG_SIZE_EXCEEDED_NUM_OF_REQ_REJECTED, CC_OUT_REQ_LOOP_PREVENTED,
             CC_OUT_REQ_PEER_GROUP_LOOP_PREVENTED, CC_OUT_REQ_TOO_BUSY, CC_OUT_REQ_UNABLE_TO_DELIVER,
             CC_OUT_REQ_PEER_GROUP_UNABLE_TO_DELIVER, CC_OUT_REQ_NUM_OF_TRANSACTIONS_REJECTED,
             CC_OUT_REQ_THROTTLING_REJECTED, CC_OUT_REQ_DOIC_THROTTLING_REJECTED,
             CC_OUT_REQ_PEER_GROUP_THROTTLING_REJECTED, CC_OUT_REQ_PEER_GROUP_DOIC_THROTTLING_REJECTED,
             CC_IN_REQ_ROAMING_PARTNER_ID_CHECKS_REJECTED, CC_OUT_REQ_ROAMING_PARTNER_ID_CHECKS_REJECTED,
             CC_IN_REQ_LOCAL_ID_CHECKS_REJECTED, CC_OUT_REQ_LOCAL_ID_CHECKS_REJECTED, CC_OUT_ANS_HX_BD_INITIALIZE_SUCC,
             CC_OUT_ANS_HX_BD_INITIALIZE_UNSUCC, CC_OUT_ANS_HX_BD_BINDING_SUCC, CC_OUT_ANS_HX_BD_BINDING_UNSUCC,
             CC_OUT_ANS_HX_BD_VERIFY_SUCC, CC_OUT_ANS_HX_BD_VERIFY_UNSUCC, CC_OUT_ANS_HX_BD_TERMINATE_SUCC,
             CC_OUT_ANS_HX_BD_TERMINATE_UNSUCC, CC_OUT_ANS_HX_TR, CC_OUT_ANS_HX_ERROR])
        partC = agg.sum_counters([CC_NUM_OF_GENERATED_ANS_DROPPED])
        partD = partA + partB - partC
        DSCKPI_TRAFFIC_TRANSACTION_SUCCESS_RATE = agg.success_rate(partD, (
                DSCKPI_NUMBER_OF_TRAFFIC_TRANSACTIONS_PER_SECOND_partA - DSCKPI_NUMBER_OF_TRAFFIC_TRANSACTIONS_PER_SECOND_partB))
        print("partD :: ", partD)
        print("DSCKPI_NUMBER_OF_TRAFFIC_TRANSACTIONS_PER_SECOND_partC ::: ", (
                DSCKPI_NUMBER_OF_TRAFFIC_TRANSACTIONS_PER_SECOND_partA - DSCKPI_NUMBER_OF_TRAFFIC_TRANSACTIONS_PER_SECOND_partB))

        partA = agg.sum_counters([CC_OUT_ANS_NUM_OF_MSGS_SENT]) - agg.sum_counters([CC_OUT_ANS_NUM_OF_MSGS_EBIT_SET])
        partB = agg.sum_counters([CC_IN_REQ_NUM_OF_MSGS_RECEIVED])

        PEERKPI_INCOMING_TRANSACTION_SUCCESS_RATE_PER_PEER = agg.success_rate(partA, partB)
        partA = agg.sum_counters([CC_IN_ANS_NUM_OF_MSGS_RECEIVED]) - agg.sum_counters([CC_IN_ANS_NUM_OF_MSGS_EBIT_SET])
        partB = agg.sum_counters([CC_OUT_REQ_NUM_OF_MSGS_SENT])

        PEERKPI_OUTGOING_TRANSACTION_SUCCESS_RATE_PER_PEER = agg.success_rate(partA, partB)

        print(f"CC_IN_REQ_NUM_OF_MSGS_RECEIVED: {agg.sum_counters([CC_IN_REQ_NUM_OF_MSGS_RECEIVED])}")
        print(f"CC_OUT_ANS_NUM_OF_MSGS_SENT: {agg.sum_counters([CC_OUT_ANS_NUM_OF_MSGS_SENT])}")
        #
        # CALCULATE Composite KPIs and WRITE to Kafka file
        #
        self.add_kafka_kpi(kafka_data_source_builder, KpiAndValue("DSCKPI_NUMBER_OF_TRAFFIC_TRANSACTIONS_PER_SECOND",
                                                                  DSCKPI_NUMBER_OF_TRAFFIC_TRANSACTIONS_PER_SECOND))
        self.add_kafka_kpi(kafka_data_source_builder, KpiAndValue("DSCKPI_TRAFFIC_TRANSACTION_SUCCESS_RATE",
                                                                  DSCKPI_TRAFFIC_TRANSACTION_SUCCESS_RATE))
        self.add_kafka_kpi(kafka_data_source_builder, KpiAndValue("PEERKPI_NUMBER_OF_TRANSACTIONS_PER_SECONDS_PER_PEER",
                                                                  PEERKPI_NUMBER_OF_TRANSACTIONS_PER_SECONDS_PER_PEER))
        self.add_kafka_kpi(kafka_data_source_builder, KpiAndValue("PEERKPI_INCOMING_TRANSACTION_SUCCESS_RATE_PER_PEER",
                                                                  PEERKPI_INCOMING_TRANSACTION_SUCCESS_RATE_PER_PEER))
        self.add_kafka_kpi(kafka_data_source_builder, KpiAndValue("PEERKPI_OUTGOING_TRANSACTION_SUCCESS_RATE_PER_PEER",
                                                                  PEERKPI_OUTGOING_TRANSACTION_SUCCESS_RATE_PER_PEER))

    def write_pod_status_kpi(self, kafka_data_source_builder: KafkaDataSourceBuilder):
        STATUS_UNDEFINED = "undefined"
        status = STATUS_UNDEFINED
        kpi = 0
        out, error = self.subprocess_obj.get_output_with_run(f"""kubectl get pods -n {self.namespace} --no-headers""")
        try:
            if error:
                raise ValueError(f'Failed fetching pods information, error: {error}')
            logging.info(f"Command output : {str(out)}")

            for line in out.splitlines():
                logging.info(f"Command output : {str(line)}")
                fields = line.strip().split()
                if not "eric-data-search-engine-curator" in fields[0]:
                    status = fields[2] if len(fields) > 2 else "undefined"
                    if status not in ["", "Running", "Completed", "ContainerCreating"]:
                        kpi = 1
                        break
            logging.info(f"KPI: CTA_PROCESS_HC = {kpi}, status is: {status}")
            self.add_kafka_kpi(kafka_data_source_builder, KpiAndValue("CTA_PROCESS_HC", kpi))

        except Exception as err:
            logging.exception(f"Failed to fetch status of pods : {str(err)}")

    def host_verification_check(self, ip):
        cmd = f"ssh-keygen -R {ip} -f /home/ericuser/.ssh/known_hosts"
        out, err = self.subprocess_obj.execute_cmd(cmd)
        if err:
            logging.error(f"Host verification Failed...{str(err)}")
            return False
        return True

    def dsc_hostname_peer_kpi(self, kafka_data_source_builder: KafkaDataSourceBuilder, dsc_ip: str, dsc_user: str,
                              dsc_pass: str):
        kpi = 0
        loc = 1
        login_successful = False
        peer_list = ""
        max_try = 5
        counter = 0
        login = f'ssh dsc-admin@{dsc_ip}'
        child = pexpect.spawn(login)
        h = -1
        while h != 3:
            h = child.expect(
                [r".*Host key verification failed.*", r'.*assword.*', r'.*fingerprint.*', r'.* connected from.*',
                 r'.*Disconnected from.*', pexpect.TIMEOUT, pexpect.EOF, 'Connection refused by peer',
                 'Connection refused by server', "connection reset by peer"])
            if h == 1:
                child.sendline(dsc_pass)
            elif h == 2:
                child.sendline("yes")
            elif h == 3:
                login_successful = True
            elif h == 4:
                break
            elif h == 0:
                print(f"Host verification failed...")
                logging.info(f"Host verification failed...Working on resolution...!")
                host_verification_check = self.host_verification_check(dsc_ip)
                if not host_verification_check:
                    break
                child = pexpect.spawn(login)
            else:
                print(f"h = {str(h)}")
            counter += 1
            if counter >= max_try:
                break
        if login_successful:
            master = ""
            instance = ""
            instance_activated = False
            instance_counter = 0
            child.sendline('paginate false')
            child.expect('#')
            child.sendline(
                f'show dsc-function dsc-nodes dsc-node {dsc_user} dsc-adjacent-realms dsc-adjacent-realm | nomore')
            child.expect('#', timeout=250)
            peer_list = child.before.decode('utf-8')
            peer_list = peer_list.split("\r\n")
            try:
                logging.info(f"peer_list = {str(peer_list)}")
                if " closed" in str(peer_list) or " opening" in str(peer_list):
                    for i, line in enumerate(peer_list):
                        if instance_activated:
                            instance_counter += 1

                        if "dsc-adjacent-realms" in line:
                            master = line
                            instance_counter = 0
                            instance_activated = False
                            continue

                        if "dsc-remote-peers" in line:
                            master = master + line
                            instance_counter = 0
                            instance_activated = False
                            continue

                        if "dsc-remote-peer-instance" in line:
                            instance = line
                            instance_activated = True
                            # instance_counter += 1
                            continue

                        if "dsc-remote-peer" in line:
                            loc = i
                            instance_counter = 0
                            instance_activated = False
                            continue

                        if "connection-state closed" in line or "connection-state opening" in line or "connection-state closing" in line:
                            logging.info(
                                f"loc: {str(peer_list[loc])}, current_line = {i}, instance_counter= {str(instance_counter)}")
                            cmd = master + ' '.join(
                                item for item in peer_list[loc:i - instance_counter] if "connection-state" not in item)
                            # cmd = master + ' '.join(peer_list[loc:i - instance_counter])
                            cmd = f"show running-config dsc-function dsc-nodes dsc-node {dsc_user} " + str(
                                cmd) + instance + " | context-match administrative-state"
                            logging.info(f"{i} at location, cmd: {str(cmd)} and line is : {str(line)}")
                            instance = ""
                            # loc = i + 1
                            child.sendline(cmd)
                            child.expect('#')
                            locked_unlocked_stat_data = child.before.decode('utf-8')
                            logging.info(f"locked_unlocked_stat_data: {str(locked_unlocked_stat_data)}")
                            if "administrative-state" not in str(locked_unlocked_stat_data):
                                continue
                            locked_unlocked_stat_data = locked_unlocked_stat_data.split("\r\n")
                            logging.info(f"locked_unlocked_stat_data: {str(locked_unlocked_stat_data)}")
                            for lo, li in enumerate(locked_unlocked_stat_data):
                                if lo == 0:
                                    continue
                                if "administrative-state" in li:
                                    if "unlocked" in li:
                                        kpi = 1
                                        logging.info(f"kpi: {str(kpi)}")
                                        break
                            if kpi == 1:
                                break

                        if "connection-state open" in line:
                            # loc = i + 1
                            instance = ""
                            continue

            except Exception as err:
                logging.exception(f"Failed to fetch status of pods : {str(err)}")
                kpi = 0

            child.sendline('exit')
            child.expect(pexpect.EOF)
            logging.info(f"KPI: DSC_HOSTNAME_PEER_CONN = {str(kpi)}")
            self.add_kafka_kpi(kafka_data_source_builder, KpiAndValue("DSC_HOSTNAME_PEER_CONN", kpi))

        else:
            logging.info(f"DSC_HOSTNAME_PEER_CONN -> LOGIN FAILED...{child.before.decode('utf-8')}")

    def set_message(self, data_source_hostname, data_source_ip, kafka_data_source_builder: KafkaDataSourceBuilder):
        kafka_data_source_builder.set_message_field("kpi_last_updated_date", self.todayUTC)
        kafka_data_source_builder.set_message_field("kpi_source",
                                                    f'{data_source_hostname} > KPI_CSA.py > {self.utcTimestamp}')
        kafka_data_source_builder.set_message_field("config_item", self.host_name)
        kafka_data_source_builder.set_message_field("kpi_info", f'{data_source_hostname} {data_source_ip}')
        kafka_data_source_builder.set_message_field("src_modified_dt", self.todayUTCMilli)
        kafka_data_source_builder.set_message_field("local_modified_dt", self.localNowMilli)

    def main(self, pm_bulk, kafka_data_source_builder: KafkaDataSourceBuilder, dsc_ip: str, dsc_user: str,
             dsc_pass: str):
        cmd: str = ""

        logging.info(f'PM-BULK NAME - {pm_bulk}')

        # Get hostname of air pod
        try:
            cmd = f"""env | grep "HOSTNAME=" | awk -F'=' '{{print $2}}' """
            ip_hostname_csv, error = self.execute_kubectl(pm_bulk, cmd)
            if ip_hostname_csv:
                data_source_hostname = ip_hostname_csv.strip()
                cmd = f"""grep {data_source_hostname} /etc/hosts | awk -F' ' '{{print $1}}' """
                host_by_name, error = self.execute_kubectl(pm_bulk, cmd)
                data_source_ip = host_by_name.strip()
            else:
                data_source_hostname = "NOT AVAILABLE"
                data_source_ip = "NOT AVAILABLE"
            logging.info(f"Hostname: {data_source_hostname}, IP: {data_source_ip}")
            self.set_message(data_source_hostname.upper(), data_source_ip, kafka_data_source_builder)
        except Exception as err:
            logging.error(f"Exception {str(pm_bulk)} ::: {str(err)}")

        # Checking
        try:
            cmd = """ip addr show eth1 | grep -w inet | wc -l """
            count, error = self.subprocess_obj.execute_cmd(cmd)
            count = count.strip()
            if int(count) == 1:
                logging.info("Not an active director node, exiting...")
                sys.exit(0)
        except Exception as err:
            logging.error(f"Exception {cmd} ::: {str(err)}")

        self.write_pod_status_kpi(kafka_data_source_builder)
        self.dsc_hostname_peer_kpi(kafka_data_source_builder, dsc_ip, dsc_user, dsc_pass)

        file_paths = files_newer_that_mins(self.pm_files_local_dir, "*.xml.*", self.execution_period_mins)
        self.aggregate_pm_files_into_csv_file(pm_bulk, file_paths)
        self.write_pm_kpis(kafka_data_source_builder, self.execution_period_mins)