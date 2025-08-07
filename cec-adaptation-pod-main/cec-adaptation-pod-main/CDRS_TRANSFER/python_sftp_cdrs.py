import os
import json
import time
import paramiko
import subprocess
from pathlib import Path
import logging
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from lib.process_check.ProcessCheck import ProcessCheck


class SFTPClient:
    def __init__(self, config, namespace):
        self.namespace = namespace
        self.primary_host = config[self.namespace]["primary_host"]
        self.secondary_host = config[self.namespace]["primary_host"]
        self.port = config["port"]
        self.username = config["username"]
        self.password = config["password"]
        self.file_types = config["file_types"]
        self.remote_directory_map = config["remote_directory_map"]
        self.transport = None
        self.connection = None
        self._logger = logging.getLogger()

    def connect(self):
        for host in [self.primary_host, self.secondary_host]:
            if not host:
                continue
            try:
                self._logger.info(f"Trying to connect to {host}...")
                self.transport = paramiko.Transport((host, self.port))
                self.transport.connect(username=self.username, password=self.password)
                self.connection = paramiko.SFTPClient.from_transport(self.transport)
                self._logger.info(f"Connected to {host}")
                return
            except Exception as e:
                self._logger.error(f"Connection failed to {host}: {e}")
        raise ConnectionError("Failed to connect to both primary and secondary hosts.")

    def upload_and_rename(self, local_path, extension):
        original_filename = os.path.basename(local_path)
        remote_dir = self.remote_directory_map.get(extension)
        if not remote_dir:
            self._logger.info(f"No remote path mapped for extension {extension}")
            return False

        remote_tmp_path = os.path.join(remote_dir, original_filename + ".tmp")
        remote_final_path = os.path.join(remote_dir, original_filename)
        self._logger.info(f"remote_tmp_path: {remote_tmp_path}")
        self._logger.info(f"remote_final_path: {remote_final_path}")

        try:
            self.connection.put(local_path, remote_tmp_path)
            self._logger.info(f"Uploaded: {local_path} --> {remote_tmp_path}")

            self.connection.rename(remote_tmp_path, remote_final_path)
            self._logger.info(f"Renamed remote file: {remote_tmp_path} --> {remote_final_path}")
            return True
        except Exception as e:
            self._logger.error(f"Upload failed for {local_path}: {str(e)}")
            return False

    def close(self):
        if self.connection:
            self.connection.close()
        if self.transport:
            self.transport.close()


class SFTPUploader:
    def __init__(self, config_path, namespace, logger):
        self.namespace = namespace
        self._logger = logger
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.root_directory = self.config["root_directory"]
        self.clients = {
            name: SFTPClient(cfg, self.namespace)
            for name, cfg in self.config["sftp_connections"].items()
        }

    def removeFile(self, source_local_path: str) -> bool:
        try:
            _ = subprocess.run("sudo rm " + source_local_path, shell=True)
            self._logger.info(f'Removed File Successfully from : {str(source_local_path)}')
            return True
        except Exception as err:
            self._logger.error(f"ERROR WHILE REMOVING FILE: {str(err)}")
            return False

    def run(self):
        start_time = time.time()
        max_runtime = 14 * 60  # 14 minutes in seconds

        for conn_name, client in self.clients.items():
            try:
                client.connect()
            except Exception as e:
                self._logger.error(f"[{conn_name}] Unable to establish connection: {e}")
                continue

        try:
            for dirpath, _, filenames in os.walk(self.root_directory, topdown=False):
                for file in filenames:
                    elapsed_time = time.time() - start_time
                    if elapsed_time >= max_runtime:
                        self._logger.info(f"Time limit reached ({elapsed_time:.2f}s). Exiting gracefully.")
                        return

                    file_path = os.path.join(dirpath, file)
                    ext = Path(file).suffix.upper()

                    for conn_name, client in self.clients.items():
                        if ext in client.file_types and client.connection:
                            self._logger.info(f"[{conn_name}] [{client}] Processing {file_path}")
                            success = client.upload_and_rename(file_path, ext)
                            if success:
                                self.removeFile(file_path)
                                self._logger.info(f"Deleted local file: {file_path}")
                            break

                # Remove empty folder
                if not os.listdir(dirpath):
                    if dirpath != self.root_directory:
                        os.rmdir(dirpath)
                        self._logger.info(f"Removed empty folder: {dirpath}")

        finally:
            for client in self.clients.values():
                client.close()
            self._logger.info("All SFTP connections closed.")


def get_namespace():
    cmd = "kubectl get ns | egrep '.*cafgp.*|caf.*-system' | awk -F' ' '{print $1}'"
    res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
    ns, error = res.communicate()

    if error:
        raise Exception(error)

    if ns == "":
        raise Exception("No Namespace found!")

    ns = str(ns).strip()

    return ns


if __name__ == "__main__":
    pc = ProcessCheck(os.path.join("/", "tmp", os.path.basename(os.path.dirname(os.path.abspath(__file__))) + ".pid"))
    pc.start()
    script_dir = os.path.dirname(__file__)
    config_file_path = os.path.join(script_dir, 'config.json')

    logging.basicConfig(level=logging.INFO, filename=f'{str(script_dir)}/python_sftp_cdrs.log', filemode='w',
                        format='%(asctime)s - %(name)s - %('
                               'levelname)s - %(lineno)d - %(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S')

    logger = logging.getLogger()

    # namespace
    namespace = get_namespace()
    logger.info(f"namespace:::: {namespace}")

    uploader = SFTPUploader(config_file_path, namespace, logger)
    uploader.run()
    pc.stop()
