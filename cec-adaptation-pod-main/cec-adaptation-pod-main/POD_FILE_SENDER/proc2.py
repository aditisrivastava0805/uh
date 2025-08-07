import logging
import os
import subprocess
from typing import Tuple
import paramiko


def execute(cmd) -> Tuple[str, str, int]:
    proc: subprocess.Popen[str] = subprocess.Popen(cmd, shell=True, universal_newlines=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    logging.info(f'Execute: "{cmd}"')

    out, err = proc.communicate(cmd)

    if proc.returncode:
        logging.error(f'Failed cmd: {cmd}, error: {err}')

    return out, err, proc.returncode


def eval_value(raw_value: str) -> str:
    CMD_KEY = 'cmd:'

    if raw_value.startswith(CMD_KEY):
        command = raw_value.split(CMD_KEY)[-1]
        value, err, exit_code = execute(command)

        if err:
            raise OSError(exit_code, err)

        return value.strip()
    else:
        return raw_value

def convert_xml_gz_to_xml(gz_file: str, output_path: str) -> str:
    logging.info(f'convert_xml_gz_to_xml: "{str(gz_file)}"')
    if str(gz_file).endswith(".xml"):
        return gz_file

    logging.info(f'convert_xml_gz_to_xml converting xml.gz to .xml')
    filename = os.path.basename(gz_file)
    xml_file_path = os.path.join(output_path, filename)
    cmd = f"cp {gz_file} {xml_file_path}"
    value, err, exit_code = execute(cmd)

    cmd = f"gunzip {xml_file_path}"
    value, err, exit_code = execute(cmd)

    xml_file_path = str(xml_file_path).replace(".gz", "")
    return xml_file_path


def sftp_transfer(sftp_hostname, sftp_user, sftp_pass, source_path, dest_path, filenames_list):
    logging.info(f"Filename List:::{str(filenames_list)}")
    try:
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(sftp_hostname, username=sftp_user, port=9022, password=sftp_pass)
            with ssh.open_sftp() as sftp:
                for filename in filenames_list:
                    filename = os.path.basename(filename)
                    source_file_path = os.path.join(source_path, filename)
                    dest_file_path = os.path.join(dest_path, filename)
                    logging.info(f"source_file_path:::{str(source_file_path)}")
                    logging.info(f"dest_file_path:::{str(dest_file_path)}")
                    sftp.get(source_file_path, dest_file_path)
        return True
    except Exception as err:
        logging.error(f'exception occurred in sftp_transfer::: {str(err)}')
        return False