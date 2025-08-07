import logging
import os
import re
from typing import NamedTuple, List, Tuple, Optional

from proc2 import execute, eval_value, sftp_transfer

Container = NamedTuple('Container', name=str, pod=str, namespace=str)


def cont_str(container: Container):
    return "/".join(container)


def kubectl_cmd():
    return 'kubectl'


def exec_kube(cmd, cont: Container) -> Tuple[str, str, int]:
    cmd = f"""{kubectl_cmd()} exec {cont.pod} -c {cont.name} -n {cont.namespace} -- {cmd}"""
    return execute(cmd)


def pod_get_cmd(ns: str) -> str:
    namespace_option = f"-n {ns}" if ns else ""
    return f'{kubectl_cmd()} get pod {namespace_option} --no-headers -o custom-columns="containers:spec.containers[*].name, name:metadata.name, name:metadata.namespace"'


def helm_hostname(ns: str) -> Optional[str]:
    if ns == "csa":
        cmd = f"""helm get values `helm ls -n {ns} | grep {ns} |  awk '{{print $1}}'` -n {ns} | grep applicationId | awk 'NR==1{{print $2}}' | awk -F- '{{print $1}}'"""
    else:
        cmd = f"""helm get values `helm ls -n {ns} | grep eric-cloud-native-base | awk '{{print $1}}'` -n {ns} | grep applicationId | tail -n 1 | awk '{{print $2}}'"""
    hostname, error, exit_code = execute(cmd)

    if error:
        logging.error(f"Could not fetch hostname from helm, error: {error}")
        return None

    hostname = hostname.strip().upper()

    logging.info(f'Hostname from helm: {hostname}')

    return hostname


def fetch_files(cont: Container, source_folder, file_newer_than_mins, dest_folder) -> Optional[List[str]]:
    tar_cmd = f"""tar -zcf - --transform='flags=r;s/$/.tmp/' --newer-mtime '{file_newer_than_mins} mins ago' -C {source_folder} . | tar -zxvf - --no-overwrite-dir -C {dest_folder}"""
    out, error, exit_code = exec_kube(tar_cmd, cont)

    if exit_code:
        logging.error(f'Failed fetching files from pod {cont_str(cont)}, error: {error}')
        return None

    file_paths = []
    for file_path in out.splitlines():
        filename = os.path.basename(file_path)
        if filename:
            file_paths.append(filename)

    logging.info(f"Files fetched: {file_paths}")

    return file_paths


def fetch_files_using_sftp(cont: Container, source_folder, file_newer_than_mins, dest_folder, sftp_dict) -> Optional[
    List[str]]:
    latest_file_cmd = f"""find {source_folder} -type f -mmin -{file_newer_than_mins} """
    out, error, exit_code = exec_kube(latest_file_cmd, cont)

    if exit_code:
        logging.error(f'Failed fetching files from pod {cont_str(cont)}, error: {error}')
        return None, False

    host = eval_value(sftp_dict["HOSTNAME_PATTERN"])
    status = sftp_transfer(host, sftp_dict["USERNAME"], sftp_dict["PASSWORD"], source_folder, dest_folder,
                           out.splitlines())

    if not status:
        return None, False

    file_paths = []
    for file_path in out.splitlines():
        filename = os.path.basename(file_path)
        if filename:
            file_paths.append(filename)

    logging.info(f"Files fetched: {file_paths}")

    return file_paths, True


def select_containers(cont, pod, ns) -> Optional[List[Container]]:
    logging.info(f'Select containers by pattern, container: {cont}, pod: {pod}, ns: {ns}')

    out, error, exit_code = execute(pod_get_cmd(ns))

    if exit_code:
        logging.error(f"Failed fetching PODs, error: {error}")
        return None

    containers: List[Container] = filter_containers(out, cont, pod, ns)

    return containers


def filter_containers(containers_text, container_filter, pod_filter, namespace_filter) -> List[Container]:
    logging.info(f"Filtering containers, name: {container_filter}, pod: {pod_filter}, ns: {namespace_filter}")

    containers = []

    for row in containers_text.splitlines():
        container_multi_name = row.split()
        for container_name in container_multi_name[0].split(','):
            containers.append(Container(container_name, container_multi_name[1], container_multi_name[2]))

    container_pattern = re.compile(container_filter)
    pod_pattern = re.compile(pod_filter)
    namespace_pattern = re.compile(namespace_filter)

    return list(filter(
        lambda c: container_pattern.match(c.name) and pod_pattern.match(c.pod) and namespace_pattern.match(c.namespace),
        containers))
