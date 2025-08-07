import traceback

from Logger import LoggingHandler
import paramiko
from paramiko import AutoAddPolicy, SSHClient


class SftpClass:
    def __init__(self, sftp_user: str, sftp_password: str, ip_address):
        """
        SftpClass Constructor - Loading when class loads.
        Loading required class and getiing sftp information from configuration file.

        :param ip_address: IP Address for Splunk Forwarder Pod
        :param sftp_user: SFTP user.
        :param sftp_password: SFTP password.
        :return None
        """
        self.client = None
        self._sftp_connection_alive = False
        self._logger = LoggingHandler.get_logger(self.__class__.__name__)
        self._logger.info("Inside __init__()..")
        self._sftp_connection = None
        self.hostname = ip_address
        self.user = sftp_user
        self.passwd = sftp_password
        self._logger.info("In the end of __init__ ")

    def connection(self):
        """
        Creating the sftp connection

        :return: SFTP Connection
        """
        try:
            client = SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(AutoAddPolicy())
            client.connect(
                self.hostname,
                username=self.user,
                password=self.passwd,
                timeout=5000,
                banner_timeout=60
            )
            sftp_conn = client.open_sftp()
            return sftp_conn
        except paramiko.ssh_exception.AuthenticationException:
            pass
        except Exception as err:
            self._logger.error(f"Exception in create_sftp_connection() while creating a connection ::: {str(err)}")

    def upload_files(self, conn, uid, gid, local_path, remote_path):
        """
        Uploading the file and changing the permission of the file.

        :param conn: SFTP Connection object.
        :param uid: User ID of the folder.
        :param gid: Group ID of the folder.
        :param local_path: Local file path.
        :param remote_path: Remote file path.
        :return: True/False based on success condition, Error details if there is any otherwise None
        """
        try:
            if conn is not None:
                conn.put(local_path, remote_path)
                conn.chown(remote_path, uid, gid)
                self._logger.info(f"File has been uploaded and permission changed UID {str(uid)} and GID {str(gid)}")
                return True, None
        except AttributeError:
            return False, "AttributeError"
        except ConnectionResetError:
            return False, "ConnectionResetError"
        except paramiko.ssh_exception.BadHostKeyException:
            return False, "paramiko.ssh_exception.BadHostKeyException"
        except paramiko.ssh_exception.SSHException:
            return False, "paramiko.ssh_exception.SSHException"
        except EOFError:
            return False, "EOFError"
        except OSError as error:
            return False, f"OSError: {str(error)}"
        except Exception as err:
            self._logger.error(f"Exception in upload_files() ::: {str(err)}")
            self._logger.error(traceback.format_exc())
            return False, f"{type(err).__name__}:{str(err)}"
