"""
Python versions of common bash commands to avoid security issues with os.system
or popen.
"""

import os
import shutil
import glob
import re
from collections import deque

from typing import List


def unglob(pattern: str) -> List[str]:
    if "*" in str(pattern):
        expanded = glob.glob(pattern)
    else:
        expanded = [pattern]
    return expanded


def grep(pattern: str, filename: str, tail=-1, head=-1, match_only=False) -> List[str]:
    found_lines = []
    for file in unglob(filename):
        grep_one_file(pattern, file, match_only, found_lines)

    if tail > 0:
        return found_lines[-tail:]
    if head > 0:
        return found_lines[:head]
    return found_lines


def get_file_basename(file: str):
    return os.path.basename(os.path.abspath(file))


def grep_one_file(pattern: str, file: str, match_only: bool, found_lines: List[str]):
    regex = re.compile(pattern)
    with open(file, "r") as fh:
        for line in fh:
            match = regex.search(line)
            if match:
                if match_only:
                    found_lines.append(match.group(0))
                else:
                    found_lines.append(line)


def tail(file: str, n=10) -> List[str]:
    buffer = deque(maxlen=n)
    with open(file, "r") as fh:
        while True:
            line = fh.readline()
            if not line:
                break
            buffer.append(line)
    return list(buffer)


def head(file: str, n=10) -> List[str]:
    with open(file, "r") as fh:
        lines = [fh.readline() for _ in range(n)]

    # if the number of lines in the file is less than n, remove the trailing
    # blank lines read in
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def rm(files: str):
    for file in unglob(files):
        if os.path.isfile(file):
            os.remove(file)
        else:
            shutil.rmtree(file)


def mv(files: str, destination: str):
    for file in unglob(files):
        if os.path.isdir(destination):
            shutil.move(file, f"{destination}/{get_file_basename(file)}")
        else:
            shutil.move(file, destination)


def are_the_same_file(file1: str, file2: str) -> bool:
    if os.path.isdir(file2):
        file2 = f"{file2}/{get_file_basename(file1)}"

    if os.path.isfile(file1) and os.path.isfile(file2):
        if os.path.samefile(file1, file2):
            return True
    return False


def cp(files: str, destination: str):
    for file in unglob(files):
        if are_the_same_file(file, destination):
            continue
        if os.path.isdir(destination):
            shutil.copy(file, f"{destination}/{get_file_basename(file)}")
        else:
            shutil.copy(file, destination)


def ln(files: str, destination: str):
    for file in unglob(files):
        if are_the_same_file(file, destination):
            continue
        dest = destination
        if os.path.isdir(destination):
            dest = f"{destination}/{get_file_basename(file)}"

        if os.path.exists(dest):
            rm(dest)
        os.symlink(file, dest)


def mkdir(directory):
    if not os.path.exists(directory):
        os.mkdir(directory)
