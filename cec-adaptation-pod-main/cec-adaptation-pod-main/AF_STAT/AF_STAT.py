
import os
from Logger import LoggingHandler
from SubprocessClass import SubprocessClass
from SftpClass import SftpClass
from typing import Any, Dict, List


class AF_STAT:
    def __init__(self, namespace, script_dir: str, sftp_user: str, sftp_password: str, sftp_hostname: str, file_newer_than_min: int, output_dir: str, dir_lookup, uid, gid):
        self._logger = LoggingHandler.get_logger(self.__class__.__name__)
        self.namespace = namespace
        self.script_dir = script_dir
        self.file_newer_than_min = file_newer_than_min
        self.local_dir = output_dir
        self.dir_lookup = dir_lookup
        self.uid = uid
        self.gid = gid
        self.subprocess_obj = SubprocessClass()
        self.sftp_connection = SftpClass(sftp_user, sftp_password, sftp_hostname)

    def get_files_from_pod(self, pod_name: str, file_newer_than_min: int, file_path_on_pod: str, filetypes, local_dir: str):
        try:
            if not os.path.isdir(local_dir):
                # Creating the folder if not there
                os.makedirs(local_dir, exist_ok=True)
            for filetype in filetypes:
                # cmd = f"""kubectl exec {pod_name} -- tar -zcf - --newer-mtime '{str(file_newer_than_min)} mins ago' -C {str(file_path_on_pod)} . | tar -zxvf - -C {local_dir}/ """
                cmd = f"""kubectl exec -n {self.namespace} {pod_name} -- bash -c "cd {file_path_on_pod} ;find ./ -type f -name '{filetype}' -mmin -{str(file_newer_than_min)} | tar -zcf - --transform='flags=r;s|^./|{pod_name}_|' -T -" -- | tar -zxvf - --no-overwrite-dir -C {local_dir} """
                self._logger.info(f"Command :::: {str(cmd)}")
                out, err = self.subprocess_obj.execute_cmd(cmd)
                self._logger.info(f"out::: {str(out)}     error : {str(err)}")
            return True
        except Exception as err:
            self._logger.info(f"Exception in get_files() ::: {str(err)}")
            return False

    def main(self, pod_name: str):
        try:
            conn = self.sftp_connection.connection()
            for pod_folder_path in self.dir_lookup.keys():
                if not self.dir_lookup[pod_folder_path]["splunk_backup_dir"].endswith("/"):
                    self.dir_lookup[pod_folder_path]["splunk_backup_dir"] = self.dir_lookup[pod_folder_path][
                                                                           "splunk_backup_dir"] + "/"
                folder_name = self.dir_lookup[pod_folder_path]["splunk_backup_dir"].split("/")[-2]
                local_file_path = os.path.join(self.local_dir, folder_name)
                if self.get_files_from_pod(pod_name, self.file_newer_than_min, pod_folder_path, self.dir_lookup[pod_folder_path]["search_keyword_for_file"], local_file_path):
                    for file_name in os.listdir(local_file_path):
                        local_dir_and_filename = os.path.join(local_file_path, file_name)
                        splunk_dir_and_filename = os.path.join(self.dir_lookup[pod_folder_path]["splunk_backup_dir"], file_name)
                        file_transfer_status, transfer_error = self.sftp_connection.upload_files(conn, self.uid, self.gid, local_dir_and_filename, splunk_dir_and_filename)
                        self._logger.info(
                            f"file_transfer_status: {str(file_transfer_status)}, transfer_error: {str(transfer_error)}, filename: {local_dir_and_filename}")
                        if file_transfer_status:
                            os.remove(local_dir_and_filename)
            conn.close()
            self._logger.info("Connection Closed")
        except Exception as err:
            self._logger.info(f"Exception in main() ::: {str(err)}")