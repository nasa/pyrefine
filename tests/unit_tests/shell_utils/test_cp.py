import os
import filecmp
from pyrefine.shell_utils import cp, rm
from pyrefine.directory_utils import cd

test_dir = os.path.dirname(os.path.abspath(__file__))


def test_cp_same_file():
    with cd(test_dir):
        file = 'test_file'
        os.system(f'touch {file}')
        cp(file, file)
        rm(file)


def test_cp_same_file_relative_dest():
    with cd(test_dir):
        file = 'test_file'
        os.system(f'touch {file}')
        cp(file, '.')
        rm(file)


def test_cp_new_file():
    with cd(test_dir):
        file1 = 'test_file1'
        file2 = 'test_file2'
        os.system(f'echo 1 > {file1}')
        cp(file1, file2)
        assert filecmp.cmp(file1, file2)
        rm(file1)
        rm(file2)


def test_cp_overwrite_file():
    with cd(test_dir):
        file1 = 'test_file1'
        file2 = 'test_file2'
        os.system(f'echo 1 > {file1}')
        os.system(f'echo 2 > {file2}')
        cp(file1, file2)
        assert filecmp.cmp(file1, file2)
        rm(file1)
        rm(file2)


def test_cp_to_dir():
    with cd(test_dir):
        file1 = 'test_file1'
        dest = 'subdir'
        os.system(f'echo 1 > {file1}')
        cp(file1, dest)
        expected_copied_file = f'{dest}/{file1}'
        assert filecmp.cmp(file1, expected_copied_file)
        rm(file1)
        rm(expected_copied_file)


def test_cp_to_dir_overwrite():
    with cd(test_dir):
        file1 = 'test_file1'
        dest = 'subdir'
        expected_copied_file = f'{dest}/{file1}'
        os.system(f'echo 1 > {file1}')
        os.system(f'echo 2 > {expected_copied_file}')
        cp(file1, dest)
        assert filecmp.cmp(file1, expected_copied_file)
        rm(file1)
        rm(expected_copied_file)


def test_cp_glob_to_dir():
    with cd(test_dir):
        dest = 'subdir'
        for i in range(3):
            os.system(f'echo {i} > glob_file{i}')
        cp('glob_file*', dest)
        for i in range(3):
            src_file = f'glob_file{i}'
            expected_copied_file = f'{dest}/glob_file{i}'
            assert filecmp.cmp(src_file, expected_copied_file)
            rm(src_file)
            rm(expected_copied_file)


def test_cp_glob_to_dir_overwrite_files():
    with cd(test_dir):
        dest = 'subdir'
        for i in range(3):
            os.system(f'echo {i} > glob_file{i}')
            os.system(f'touch {dest}/glob_file{i}')
        cp('glob_file*', dest)
        for i in range(3):
            src_file = f'glob_file{i}'
            expected_copied_file = f'{dest}/glob_file{i}'
            assert filecmp.cmp(src_file, expected_copied_file)
            rm(src_file)
            rm(expected_copied_file)


def test_cp_relative_path_where_src_not_in_pwd():
    with cd(f'{test_dir}/subdir'):
        file = 'test_file'
        os.system(f'echo 23 > ../{file}')
        cp(f'../{file}', '.')
        assert filecmp.cmp(f'../{file}', file)
        rm(file)
        rm(f'../{file}')
