from pyrefine.shell_utils import tail, head, rm


def test_tail_and_head_small_file():
    small_file = 'small_file.txt'
    contents = '\n'.join([f'line{i}' for i in range(5)]) + '\n'
    with open(small_file, 'w') as fh:
        fh.write(contents)

    assert tail(small_file) == ['line0\n', 'line1\n', 'line2\n', 'line3\n', 'line4\n']
    assert head(small_file) == ['line0\n', 'line1\n', 'line2\n', 'line3\n', 'line4\n']

    assert tail(small_file, 2) == ['line3\n', 'line4\n']
    assert head(small_file, 2) == ['line0\n', 'line1\n']

    rm(small_file)


def test_tail_and_head_large_file():
    large_file = 'large_file.txt'
    contents = '\n'.join([f'line{i}' for i in range(100000)]) + '\n'
    with open(large_file, 'w') as fh:
        fh.write(contents)

    assert tail(large_file, 2) == ['line99998\n', 'line99999\n']
    assert head(large_file, 2) == ['line0\n', 'line1\n']

    rm(large_file)
