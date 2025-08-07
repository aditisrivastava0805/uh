import glob
import logging
import os
import time
from datetime import datetime, timedelta
from typing import List


def banner(text: str):
    return f"""{'-' * 20}  {text}  {'-' * 20}"""


def files_newer_that_mins(dir: str, file_pattern: str, newer_than_mins: int) -> List[str]:
    logging.info(banner(f"Selecting files {file_pattern} in {dir} newer than {newer_than_mins} minutes"))
    file_paths = []
    current_time = time.time()

    for file_path in glob.glob(os.path.join(dir, file_pattern)):
        time_delta = current_time - os.path.getmtime(file_path)
        if (time_delta / 60) < newer_than_mins:
            file_paths.append(file_path)

    return file_paths


def delete_files_older_than_days(dir: str, days: int):
    logging.info(f'Deleting old files, dir: {dir}, days old: {days}')
    for f in os.listdir(dir):
        file_path = os.path.join(dir, f)
        file_time = datetime.fromtimestamp(os.stat(file_path).st_mtime)
        if os.path.isfile(file_path):
            if file_time < datetime.now() - timedelta(days=days):
                os.remove(file_path)

def is_http_ok(code: str):
    return True if code[0].isdigit() and int(code[0]) < 4 else False

def is_http_error(code: str):
    return True if code[0].isdigit() and int(code[0]) >= 4 else False
