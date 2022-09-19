import os
import filecmp
from pyrefine.shell_utils import mv, rm
from pyrefine.directory_utils import cd

test_dir = os.path.dirname(os.path.abspath(__file__))


def test_mv_same_file():
    with cd(test_dir):
        file = 'test_file'
        os.system(f'touch {file}')
        mv(file, file)
        rm(file)


def test_mv_same_file_relative_dest():
    with cd(test_dir):
        file = 'test_file'
        os.system(f'touch {file}')
        mv(file, '.')
        rm(file)


def test_mv_new_file():
    with cd(test_dir):
        file1 = 'test_file1'
        file2 = 'test_file2'
        os.system(f'echo 1 > {file1}')
        mv(file1, file2)
        assert not os.path.exists(file1)
        file_contents = os.popen(f'cat {file2}').read()
        assert file_contents == '1\n'
        rm(file2)


def test_cp_overwrite_file():
    with cd(test_dir):
        file1 = 'test_file1'
        file2 = 'test_file2'
        os.system(f'echo 1 > {file1}')
        os.system(f'echo 2 > {file2}')
        mv(file1, file2)
        assert not os.path.exists(file1)
        file_contents = os.popen(f'cat {file2}').read()
        assert file_contents == '1\n'
        rm(file2)


def test_mv_to_dir():
    with cd(test_dir):
        file1 = 'test_file1'
        dest = 'subdir'
        os.system(f'echo 1 > {file1}')
        mv(file1, dest)
        expected_copied_file = f'{dest}/{file1}'
        file_contents = os.popen(f'cat {expected_copied_file}').read()
        assert file_contents == '1\n'
        assert not os.path.exists(file1)
        rm(expected_copied_file)


def test_mv_to_dir_overwrite():
    with cd(test_dir):
        file1 = 'test_file1'
        dest = 'subdir'
        expected_copied_file = f'{dest}/{file1}'
        os.system(f'echo 1 > {file1}')
        os.system(f'echo 2 > {expected_copied_file}')
        mv(file1, dest)
        file_contents = os.popen(f'cat {expected_copied_file}').read()
        assert file_contents == '1\n'
        assert not os.path.exists(file1)
        rm(expected_copied_file)


def test_mv_glob_to_dir():
    with cd(test_dir):
        dest = 'subdir'
        for i in range(3):
            os.system(f'echo {i} > glob_file{i}')
        mv('glob_file*', dest)
        for i in range(3):
            src_file = f'glob_file{i}'
            expected_copied_file = f'{dest}/glob_file{i}'
            file_contents = os.popen(f'cat {expected_copied_file}').read()
            assert file_contents == f'{i}\n'
            assert not os.path.exists(src_file)
            rm(expected_copied_file)


def test_mv_glob_to_dir_overwrite_files():
    with cd(test_dir):
        dest = 'subdir'
        for i in range(3):
            os.system(f'echo {i} > glob_file{i}')
            os.system(f'touch {dest}/glob_file{i}')
        mv('glob_file*', dest)
        for i in range(3):
            src_file = f'glob_file{i}'
            expected_copied_file = f'{dest}/glob_file{i}'
            file_contents = os.popen(f'cat {expected_copied_file}').read()
            assert file_contents == f'{i}\n'
            assert not os.path.exists(src_file)
            rm(expected_copied_file)


def test_mv_relative_path_where_src_not_in_pwd():
    with cd(f'{test_dir}/subdir'):
        file = 'test_file'
        os.system(f'echo 23 > ../{file}')
        mv(f'../{file}', '.')
        file_contents = os.popen(f'cat {file}').read()
        assert file_contents == f'23\n'
        rm(file)
        assert not os.path.exists(f'../{file}')
