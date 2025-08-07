import argparse
import sys
import os
import json
import subprocess
import re
from datetime import datetime, timedelta


class SplunkTrafficHandler:
    type_to_file_dict = {
        "SyNotification": "PSC-CIPDiameter_?.?_?_?_SyNotification.stat.0",
        "ClearDedicatedAccount": "FSC-Scheduler_*_ClearDedicatedAccount.stat.0",
        "LifeCycleChange": "FSC-Scheduler_*_LifeCycleChange.stat.0",
        "PeriodicAccountManagement": "FSC-Scheduler_*_PeriodicAccountManagement.stat.0",
        "SMSInterface": "FSC-SMSInterface_*.stat.0",
        "CIPDiameter": "PSC-CIPDiameter_?.?_?_?.stat.0",
        "ChargingRarNotification": "PSC-CIPDiameter_*_ChargingRarNotification.stat.0",
        "CIPDiameterSy": "PSC-CIPDiameter_*_Sy.stat.0",
        "AccountFinderClient": "PSC-DCIPDiameter_*_AccountFinderClient.stat.0",
        "DCIPDiameterAnchor": "PSC-DCIPDiameter_*_Anchor.stat.0",
        "DCIPDiameterRemote": "PSC-DCIPDiameter_*_Remote.stat.0",
        "PPASInterface": "PSC-PPASInterface_*.stat.0",
        "GeneratedCdrs": "PSC-TrafficHandler_*_GeneratedCdrs.stat.0",
        "PolicyReevaluation": "PSC-TrafficHandler_*_PolicyReevaluation.stat.0",
        "ChargingReauthorizationBlock": "PSC-TrafficHandler_*_ChargingReauthorizationBlock.stat.0",
        "TrafficHandler_AccountFinderClient": "PSC-TrafficHandler_*_AccountFinderClient.stat.0",
        "CIPDiameter_NchfPolicy": "PSC-CIPDiameter_*_NchfPolicy.stat.0",
        "CIPDiameter_NchfPolicyNotification": "PSC-CIPDiameter_*_NchfPolicyNotification.stat.0",
        "OfflineCDRFileHandler_InputOfflineError": "PSC-OfflineCDRFileHandler_*_InputOfflineError_GeneratedCdrs.stat.0",
        "OfflineCDRFileHandler_InputOfflineSubscriberBlocked": "PSC-OfflineCDRFileHandler_*_InputOfflineSubscriberBlocked_GeneratedCdrs.stat.0",
        "OfflineCDRFileHandler_InputOfflineSubscriberNotFound": "PSC-OfflineCDRFileHandler_*_InputOfflineSubscriberNotFound_GeneratedCdrs.stat.0",
        "OfflineCDRFileHandler_InputOfflineTimeout": "PSC-OfflineCDRFileHandler_*_InputOfflineTimeout_GeneratedCdrs.stat.0",
        "OfflineCDRFileHandler_OCCError": "PSC-OfflineCDRFileHandler_*_OnlineCreditControlError_GeneratedCdrs.stat.0",
        "OfflineCDRFileHandler_OCCSubscriberBlocked": "PSC-OfflineCDRFileHandler_*_OnlineCreditControlSubscriberBlocked_GeneratedCdrs.stat.0",
        "OfflineCDRFileHandler_OCCSubscriberNotFound": "PSC-OfflineCDRFileHandler_*_OnlineCreditControlSubscriberNotFound_GeneratedCdrs.stat.0",
        "OfflineCDRFileHandler_OCCTimeout": "PSC-OfflineCDRFileHandler_*_OnlineCreditControlTimeout_GeneratedCdrs.stat.0",
        "OfflineCDRFileHandler_OnlineCreditControl": "PSC-OfflineCDRFileHandler_*_OnlineCreditControl_GeneratedCdrs.stat.0",
        "SubscriberHandler_GeneratedCdrs": "PSC-SubscriberHandler_?.?_?_?_GeneratedCdrs.stat.0",
        "OfflineCDRFileHandler": "PSC-OfflineCDRFileHandler_?.?_?_?.stat.0",
        "TrafficHandler_InternalProviderData": "PSC-TrafficHandler_*_InternalProviderData.stat.0",
        "TrafficHandler_TimeBasedAction": "PSC-TrafficHandler_*_TimeBasedAction.stat.0",
        "UssdHD": "FSC-UssdHD_*.stat.0",
        "BCIP": "PSC-BCIP.stat.0",
        "LDAP": "PSC-LDAP_?.?_?_?.stat.0",
        "LDAP_Client": "PSC-LDAP_*_LDAPClient.stat.0"
    }
    header_dict = {
        "SyNotification": "Name SentSNR ThrputSNR FailedSNR RetransmittedSNR RecvSNA ThrputSNA Transient Permanent",
        "ClearDedicatedAccount": "SENT SUCCESS ERROR ABORT TIMEOUT DBHITS",
        "LifeCycleChange": "SENT SUCCESS ERROR ABORT TIMEOUT DBHITS",
        "PeriodicAccountManagement": "SENT SUCCESS ERROR ABORT TIMEOUT DBHITS",
        "SMSInterface": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "CIPDiameter": "Name Succ Fail Timeout Reject Retransmission Duplicate Thrput ResponsetimeAvg ResponsetimeMin ResponsetimeMax",
        "ChargingRarNotification": "Name SentRAR ThrputRAR FailedRAR RetransmittedRAR RecvRAA ThrputRAA Transient Permanent",
        "CIPDiameterSy": "Name Succ Fail Timeout Reject Retransmission Duplicate Thrput ResponseAvg ResponseMin ResponseMax",
        "AccountFinderClient": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "DCIPDiameterAnchor": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "DCIPDiameterRemote": "Name Succ Fail Timeout Reject Retransmission Duplicate Thrput ResponseAvg ResponseMin ResponseMax",
        "PPASInterface": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "GeneratedCdrs": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "PolicyReevaluation": "Name Succ Fail Reject Thrput ResponsetimeAvg ResponsetimeMin ResponsetimeMax",
        "ChargingReauthorizationBlock": "Name TotalRAR BlockedRAR",
        "TrafficHandler_AccountFinderClient": "Name Succ Fail Reject Thrput ResponsetimeAvg ResponsetimeMin ResponsetimeMax",
        "CIPDiameter_NchfPolicy": "Name Succ Fail Timeout Reject Retransmission Duplicate Thrput ResponsetimeAvg ResponsetimeMin ResponsetimeMax",
        "CIPDiameter_NchfPolicyNotification": "Name SentSNR ThrputSNR FailedSNR RetransmittedSNR RecvSNA ThrputSNA Transient Permanent",
        "OfflineCDRFileHandler_InputOfflineError": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "OfflineCDRFileHandler_InputOfflineSubscriberBlocked": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "OfflineCDRFileHandler_InputOfflineSubscriberNotFound": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "OfflineCDRFileHandler_InputOfflineTimeout": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "OfflineCDRFileHandler_OCCError": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "OfflineCDRFileHandler_OCCSubscriberBlocked": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "OfflineCDRFileHandler_OCCSubscriberNotFound": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "OfflineCDRFileHandler_OCCTimeout": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "OfflineCDRFileHandler_OnlineCreditControl": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "SubscriberHandler_GeneratedCdrs": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "OfflineCDRFileHandler": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "TrafficHandler_InternalProviderData": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "TrafficHandler_TimeBasedAction": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "UssdHD": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "BCIP": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "LDAP": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax",
        "LDAP_Client": "Name Succ Fail Reject Thrput ResponseAvg ResponseMin ResponseMax"
    }

    def __init__(self):
        # Script Path
        self.script_path = os.path.dirname(os.path.realpath(__file__))

        self.lookup_dir = "/var/log/splunk/cEC/SDP_TRAFFIC_HANDLER/"

        # Timestamp Format
        self.timestamp_format = '%Y-%m-%dT%H:%M:%SZ'
        self.UTC_TZ_OFFSET = datetime.utcnow() - datetime.now()
        if self.UTC_TZ_OFFSET.microseconds != 0:
            self.UTC_TZ_OFFSET = self.UTC_TZ_OFFSET + timedelta(microseconds=10)

        # Checkpoint log path
        self.checkpoint_log_path = self.script_path + "/logs"
        if not os.path.exists(self.checkpoint_log_path):
            os.mkdir(self.checkpoint_log_path)

    @staticmethod
    def executeShellCmd(cmd):
        result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = result.communicate()
        out = out.decode("utf-8")
        err = err.decode("utf-8")
        if out == "":
            out = None
        if err == "":
            err = None
        return out

    def convert_to_utc(self, date_time_str):
        date_time_obj = None
        if len(date_time_str) == 17:
            date_time_obj = datetime.strptime(date_time_str, '%y-%m-%d %H:%M:%S')
        elif len(date_time_str) == 15:
            date_time_str = date_time_str + "00"
            date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d-%H%M%S')

        if date_time_obj is not None:
            date_time_obj = date_time_obj + self.UTC_TZ_OFFSET
            return datetime.strftime(date_time_obj, self.timestamp_format)
        else:
            return ""

    def checkpoint_log_file_check(self, file_type):
        checkpoint_file = self.checkpoint_log_path + "/" + str(file_type) + ".ckp"
        if not os.path.exists(checkpoint_file):
            checkpoint_dict = {}
            json.dump(checkpoint_dict, open(checkpoint_file, 'w'))
        return checkpoint_file

    @staticmethod
    def write_checkpoint(checkpoint_dict, checkpoint_file, checkpoint_last_loc, checkpoint_timestamp, stat_file):
        if str(stat_file) not in checkpoint_dict.keys():
            checkpoint_dict[str(stat_file)] = {}
            value = {"timestamp": str(checkpoint_timestamp), "last_loc": checkpoint_last_loc}
            checkpoint_dict[str(stat_file)].update(value)
        else:
            checkpoint_dict[str(stat_file)]["timestamp"] = checkpoint_timestamp
            checkpoint_dict[str(stat_file)]["last_loc"] = checkpoint_last_loc
        json.dump(checkpoint_dict, open(checkpoint_file, 'w'), indent=2)

    @staticmethod
    def read_checkpoint(checkpoint_file):
        if os.path.exists(checkpoint_file):
            checkpoint_dict = json.load(open(checkpoint_file))
            return checkpoint_dict
        return None

    def read_file(self, current_file, read_pos, file_type, header_arr, response_json, checkpoint_timestamp):
        DATE = ""
        time = []
        checkpoint_last_loc = read_pos
        checkpoint_timestamp = checkpoint_timestamp
        sdp_name = str(current_file).split("_")[0]
        if os.path.exists(self.lookup_dir + current_file):
            with open(self.lookup_dir + current_file) as fp:
                if read_pos > 0:
                    fp.seek(read_pos)
                line = fp.readline().strip()
                while line:
                    # datetime may be like 2019-08-04-2051
                    date_time = re.findall(r'(^\d{4}-\d{2}-\d{2}-\d{4})', line)
                    if len(date_time) != 0:
                        checkpoint_timestamp = date_time[0]

                        # remove the datetime value
                        line = line.replace(date_time[0], "")
                        # replace "," with space
                        line = line.replace(",", " ")
                    else:
                        date = re.findall(r'(^\d{2}-\d{2}-\d{2})', line)
                        if len(date) == 0:
                            time = re.findall(r'(^\d{2}:\d{2}:\d{2})', line)
                        else:
                            DATE = date[0]

                        if len(DATE) > 0 and len(time) > 0:
                            checkpoint_timestamp = DATE + " " + time[0]

                        # maybe the last read line is a 'date' line so the date value is from the ckp point file
                        # this is only possible when the first read line is a 'time' line
                        elif len(DATE) == 0 and len(time) > 0:
                            if len(checkpoint_timestamp) > 8:
                                # has both date and time
                                checkpoint_timestamp = checkpoint_timestamp.split()[0] + " " + time[0]
                            elif len(checkpoint_timestamp) != 0:
                                # has date only
                                checkpoint_timestamp = checkpoint_timestamp + " " + time[0]

                        if len(time) > 0:
                            # 'time' line has good statistic information
                            # remove the time value from the line
                            line = line.replace(time[0], "")

                    # one of the stat files has a space in the name column
                    if "ChargingReauthorizationBlock" in file_type:
                        line = line.replace("Charging RAR", "ChargingRAR")
                    elif "AccountFinderClient" in file_type:
                        line = line.replace("Total requests", "Total_requests")
                        line = line.replace("Not found in AF", "Not_found_in_AF")
                    elif "UssdHD" in file_type:
                        line = line.replace("Total Ussd", "Total_Ussd")
                    elif "BCIP" in file_type:
                        line = line.replace("GET Total", "GET_Total")
                        line = line.replace("POST Total", "POST_Total")
                        line = line.replace("PUT Total", "PUT_Total")
                        line = line.replace("DELETE Total", "DELETE_Total")
                    elif "PolicyReevaluation" in file_type:
                        line = line.replace("Total request", "Total_request")
                        line = line.replace("Inactive session", "Inactive_session")
                        line = line.replace("Reevaluated session", "Reevaluated_session")
                    elif "TrafficHandler_TimeBasedAction" in file_type:
                        line = line.replace("TBA request", "TBA_request")
                    elif "TrafficHandler_InternalProviderData" in file_type:
                        line = line.replace("Local Provider Get", "Local_Provider_Get")
                        line = line.replace("Local Provider Update", "Local_Provider_Update")
                        line = line.replace("Local Provider Cleanup", "Local_Provider_Cleanup")
                        line = line.replace("Total internal failures", "Total_internal_failures")

                    fields = line.split()

                    # ignore the 'date' line and shorter lines
                    if len(fields) == len(header_arr):
                        # this is a complete statistic line
                        # take the read position
                        checkpoint_last_loc = fp.tell()

                        idx = 0
                        for idx in range(0, len(fields)):
                            tmp_str = fields[idx]
                            if "t-mobile" not in fields[idx]:
                                tmp_str = fields[idx].replace("-", "0")

                            if tmp_str.isdigit():
                                response_json[header_arr[idx]] = int(tmp_str)
                            else:
                                response_json[header_arr[idx]] = tmp_str
                            idx += 1
                        response_json["tl_timestamp"] = self.convert_to_utc(checkpoint_timestamp)
                        # SDP NAME
                        response_json["SDP"] = sdp_name
                        json_str = json.dumps(response_json)
                        print(json_str)
                    line = fp.readline().strip()
            return checkpoint_timestamp, checkpoint_last_loc
        return checkpoint_timestamp, checkpoint_last_loc

    def search_for_files_based_on_type(self, file_type, stat_file_regex, header_arr, response_json):
        stat_files = []
        cmd = """find lookup_dir -type f -name "*stat_file_regex" -mmin -5 """.replace("lookup_dir", self.lookup_dir).replace(
            "stat_file_regex", stat_file_regex)
        cmd_output = self.executeShellCmd(cmd)
        if cmd_output is not None:
            for line in cmd_output.splitlines():
                line = str(line).strip().split("/")[-1]
                stat_files.append(line)

        # Fetching existing checkpoint file
        checkpoint_file = self.checkpoint_log_file_check(file_type)

        # Read info from the checkpoint file
        checkpoint_dict = self.read_checkpoint(checkpoint_file)

        checkpoint_last_loc = 0
        for stat_file in stat_files:
            if str(stat_file) not in checkpoint_dict.keys():
                # checkpoint the last read information
                self.write_checkpoint(checkpoint_dict, checkpoint_file, checkpoint_last_loc,
                                      "0", stat_file)

            checkpoint_last_loc = int(checkpoint_dict[str(stat_file)]["last_loc"])
            checkpoint_timestamp = str(checkpoint_dict[str(stat_file)]["timestamp"])
            file_size = os.path.getsize(self.lookup_dir + str(stat_file))
            if int(file_size) < checkpoint_last_loc:
                current_file = str(stat_file).replace("stat.0", "stat.1")
                if os.path.exists(self.lookup_dir + current_file):
                    checkpoint_timestamp, checkpoint_last_loc = self.read_file(current_file, checkpoint_last_loc,
                                                                               file_type, header_arr, response_json,
                                                                               checkpoint_timestamp)
                    checkpoint_last_loc = 0
            checkpoint_timestamp, checkpoint_last_loc = self.read_file(stat_file, checkpoint_last_loc, file_type,
                                                                       header_arr, response_json, checkpoint_timestamp)
            self.write_checkpoint(checkpoint_dict, checkpoint_file, checkpoint_last_loc, checkpoint_timestamp,
                                  stat_file)

    def main(self, file_type):
        stat_file_regex = self.type_to_file_dict[file_type]
        header = self.header_dict[file_type]
        response_json = {}
        header_arr = header.split()
        for elem in header.split():
            response_json[elem] = ""
        self.search_for_files_based_on_type(file_type, stat_file_regex, header_arr, response_json)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="HELP Text for tool.")
    parser.add_argument("-t", "--type", help="file type: %s" % str(SplunkTrafficHandler.type_to_file_dict.keys()),
                        required=False,
                        default="")
    parser.add_argument("-f", "--format", help="json", required=False, default="json")

    try:
        argument = parser.parse_args()
    except:
        # print("Invalid command line arguments")
        sys.exit(1)

    traffic_handler_obj = SplunkTrafficHandler()
    traffic_handler_obj.main(argument.type)
    sys.exit(0)