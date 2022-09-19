"""
Python versions of common bash commands to avoid security issues with os.system
or popen.
"""
import os
import shutil
import glob
import re

from typing import List


def unglob(pattern: str) -> List[str]:
    if '*' in pattern:
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


def grep_one_file(pattern: str, file: str, match_only: bool, found_lines: List[str]):
    with open(file, 'r') as fh:
        while True:
            line = fh.readline()
            if not line:
                break
            match = re.search(pattern, line)
            if match:
                if match_only:
                    found_lines.append(match.group(0))
                else:
                    found_lines.append(line)


def tail(file: str, n=10) -> List[str]:
    with open(file, 'r') as fh:
        return fh.readlines()[-n:]


def head(file: str, n=10) -> List[str]:
    lines = []
    with open(file, 'r') as fh:
        for _ in range(n):
            lines.append(fh.readline())
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
            file_basename = os.path.basename(os.path.abspath(file))
            shutil.move(file, f'{destination}/{file_basename}')
        else:
            shutil.move(file, destination)


def are_the_same_file(file1, file2) -> bool:
    if os.path.isdir(file2):
        file_basename = os.path.basename(os.path.abspath(file1))
        file2 = f'{file2}/{file_basename}'

    if os.path.isfile(file1) and os.path.isfile(file2):
        if os.path.samefile(file1, file2):
            return True
    return False


def cp(files: str, destination: str):
    for file in unglob(files):
        if are_the_same_file(file, destination):
            continue
        if os.path.isdir(destination):
            file_basename = os.path.basename(os.path.abspath(file))
            shutil.copy(file, f'{destination}/{file_basename}')
        else:
            shutil.copy(file, destination)


def mkdir(directory):
    if not os.path.exists(directory):
        os.mkdir(directory)
