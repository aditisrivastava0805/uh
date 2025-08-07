import logging
import os.path
from typing import Optional, List

from kubernetes import cont_str, select_containers, fetch_files, fetch_files_using_sftp


def collect_files(hostname, container_pattern, pod_pattern, namespace_pattern: str, source_folder, file_newer_than_mins,
                  dest_folder, dest_filename_pattern, owner: int, group: int, sftp_dict) -> Optional[List[str]]:
    result_file_paths = []

    containers = select_containers(container_pattern, pod_pattern, namespace_pattern)

    if not containers:
        return None

    for cont in containers:
        logging.info(f'Fetching files from pod: {cont_str(cont)}')

        tar_filenames, status = fetch_files_using_sftp(cont, source_folder, file_newer_than_mins, dest_folder,
                                                       sftp_dict)
        if not status:
            tar_filenames = fetch_files(cont, source_folder, file_newer_than_mins, dest_folder)

        if not tar_filenames:
            continue

        for tar_filename in tar_filenames:
            new_filename = dest_filename_pattern.replace("{filename}", tar_filename)
            new_filename = new_filename.replace("{hostname}", hostname)
            new_filename = new_filename.replace("{namespace}", namespace_pattern)

            src_file_path = os.path.normpath(os.path.join(dest_folder, tar_filename))

            logging.info(f'Setting file user:group: {src_file_path} --> {owner}:{group}')
            os.chown(src_file_path, owner, group)

            try:
                dest_file_path = os.path.normpath(os.path.join(dest_folder, new_filename))
            except Exception as err:
                logging.error(f'collect_files() len(.tmp) is having issue: {str(err)}')

            if str(new_filename).endswith(".tmp"):
                dest_file_path = os.path.normpath(os.path.join(dest_folder, new_filename[:-len(".tmp")]))

            logging.info(f'Renaming file: {src_file_path} --> {os.path.basename(dest_file_path)}')
            os.rename(src_file_path, dest_file_path)

            result_file_paths.append(dest_file_path)

    return result_file_paths
