import numpy as np
import pytest

from pyrefine.simulation.sfe_cfg import SFEconfig


@pytest.mark.parametrize("shape", [(1, 1, 1, 3), (1, 1, 3, 1),
                                   (2, 3, 2, 4), (2, 3, 4, 2)])
@pytest.mark.parametrize("dtype", [int, float, bool])
@pytest.mark.parametrize("as_list", [False, True])
def test_four_dimensional_arrays_write_every_index(tmp_path, shape, dtype, as_list):
    values = np.arange(np.prod(shape)).reshape(shape)
    if dtype is float:
        values = values.astype(float) / 4 - 1.25
    elif dtype is bool:
        values = values % 2 == 0
    before = values.copy()
    cfg = SFEconfig()
    cfg['before'] = 7
    cfg['values'] = values.tolist() if as_list else values
    cfg['after'] = False
    output = tmp_path / 'sfe.cfg'

    cfg.write(output)

    expected_lines = ['before = 7']
    for index in np.ndindex(shape):
        key = ','.join(str(i) for i in index)
        value = values[index]
        if dtype is bool:
            value = '.true.' if value else '.false.'
        expected_lines.append(f'values({key}) = {value}')
    expected_lines.append('after = .false.')
    assert output.read_text().splitlines() == expected_lines
    restored = SFEconfig(str(output), convert_read_arrays=True)
    assert restored['values'].shape == shape
    np.testing.assert_array_equal(restored['values'], values)
    np.testing.assert_array_equal(values, before)
    assert restored['before'] == 7
    assert restored['after'] is False


@pytest.mark.parametrize("empty_axis", range(4))
def test_empty_four_dimensional_arrays_write_no_entries(tmp_path, empty_axis):
    shape = [2, 3, 2, 4]
    shape[empty_axis] = 0
    cfg = SFEconfig()
    cfg['empty'] = np.empty(shape)
    cfg['after'] = 9
    output = tmp_path / 'empty.cfg'

    cfg.write(output)

    assert output.read_text() == 'after = 9\n'


def test_noncontiguous_four_dimensional_array_round_trip(tmp_path):
    values = np.arange(120).reshape(2, 3, 4, 5)[:, ::-1, ::2, ::-1]
    assert not values.flags.c_contiguous
    cfg = SFEconfig()
    cfg['values'] = values
    output = tmp_path / 'strided.cfg'

    cfg.write(output)

    restored = SFEconfig(str(output), convert_read_arrays=True)
    assert restored['values'].shape == values.shape
    np.testing.assert_array_equal(restored['values'], values)
    assert len(output.read_text().splitlines()) == values.size
