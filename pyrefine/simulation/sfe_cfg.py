#!/usr/bin/env python
import os
from io import TextIOWrapper
from collections import OrderedDict

import numpy as np


class SFEconfig(OrderedDict):
    def __init__(self, input_file='', convert_read_arrays=False, *args, **kwargs):
        """
        Parses a SFE configuration file into a python ordered dictionary
        for querying, editing, and writing.

        NOTE: when reading/writing arrays, the reader/writer uses arrays and
        does not know the default values for every entry.  If you read
        array(1) = 1 without reading array(0), the reader will set np.zeros()
        for non-read values
        """
        self.comment_characters = ('!', '/', '#', '&')
        super().__init__(*args, **kwargs)

        if len(input_file) > 0:
            self.read(input_file, convert_read_arrays)

    def read(self, input_file='sfe.cfg', convert_read_arrays=False):
        """
        Parses a SFE configuration file into the dictionary.

        Parameters
        ----------
        input_file: str
            The name of the SFE configuration file to be read
        """
        self.input_file = input_file
        with open(input_file) as f:
            for line in f:
                line = self._remove_comments_from_line(line)
                if self._line_has_valid_key_value_pair(line):
                    (key, val) = line.split('=')
                    self[key.strip()] = self._convert_type(val.strip())

        if convert_read_arrays:
            self._convert_read_arrays_to_numpy()

    def write(self, output_file='sfe.cfg', force=False):
        """
        Writes a SFE configuration to a file.

        Parameters
        ----------
        output_file: str
            The name of the SFE configuration file to be written
        force: bool
            Force overwrite of output_file if True
        """
        if os.path.exists(output_file) and not force:
            raise FileExistsError(f'{output_file} file exist and will not be overwritten')
        else:
            with open(output_file, 'w') as fh:
                for key, value in self.items():
                    if type(value) == np.ndarray:
                        self._write_array(key, value, fh)
                    elif type(value) == list:
                        self._write_array(key, np.array(value), fh)
                    else:
                        self._write_single_value(key, value, fh)

    def _convert_read_arrays_to_numpy(self):
        self._convert_plus_sign_arrays_to_numpy()
        self._convert_parentheses_arrays_to_numpy()

    def _convert_plus_sign_arrays_to_numpy(self):
        for key, value in self.items():
            if self._value_is_a_plus_sign_array(value):
                self._convert_arrays_with_plus_signs(key, value)

    def _value_is_a_plus_sign_array(self, value) -> bool:
        if type(value) == str:
            return "+" in value
        return False

    def _convert_arrays_with_plus_signs(self, key: str, value: str):
        items = value.split('+')
        self[key] = np.array([self._convert_type(item) for item in items])

    def _convert_parentheses_arrays_to_numpy(self):
        array_keys = self._find_parentheses_array_keys()

        for key in array_keys:
            array = self._create_zeros_array_of_correct_shape_and_type(key)
            self._fill_array_from_parentheses_key(key, array)

    def _create_zeros_array_of_correct_shape_and_type(self, array_key: str):
        for key, value in self.items():
            if array_key in key:
                dtype = type(self._convert_type(value))
                ndims = key.count(',') + 1
                break

        dims = np.ones(ndims, dtype=int)
        for key in self.keys():
            if array_key == self._strip_parentheses_from_key(key):
                for dim in range(ndims):
                    dims[dim] = np.max((dims[dim], self._get_array_index(key, dim)+1))

        return np.zeros(dims, dtype=dtype)

    def _fill_array_from_parentheses_key(self, array_key: str, array: np.ndarray):
        old_keys = []
        for key, value in self.items():
            if array_key == self._strip_parentheses_from_key(key):
                ind = []
                for dim in range(array.ndim):
                    ind.append(self._get_array_index(key, dim))
                index = tuple(ind)
                array[index] = self._convert_type(value)
                old_keys.append(key)

        for key in old_keys:
            self.pop(key)
        self[array_key] = array

    def _strip_parentheses_from_key(self, key: str):
        return key.split('(')[0]

    def _get_array_index(self, key: str, dim=0):
        str_between_parentheses = key.split('(')[1].split(')')[0]
        return int(str_between_parentheses.split(',')[dim])

    def _find_parentheses_array_keys(self):
        array_keys = []
        for array_key in self.keys():
            strip_key = array_key.split('(')[0]
            if '(' in array_key and strip_key not in array_keys:
                array_keys.append(strip_key)
        return array_keys

    def _convert_type(self, val_string: str):
        if type(val_string) != str:
            return val_string

        if '.true.' == val_string.lower():
            return True
        if '.false.' == val_string.lower():
            return False
        try:
            value = int(val_string)
        except:
            try:
                value = float(val_string)
            except:
                value = val_string
        return value

    def _line_has_valid_key_value_pair(self, line: str):
        if "=" in line:
            (key, val) = line.split('=')
            if (len(key.strip()) > 0 and
                    len(val.strip()) > 0):
                return True
        return False

    def _remove_comments_from_line(self, line: str):
        for comment_character in self.comment_characters:
            line = line.split(comment_character)[0]
        return line

    def _write_array(self, array_key: str, value: np.ndarray, fh: TextIOWrapper):
        ndim = value.ndim
        if ndim == 1:
            self._write_1D_array(array_key, value, fh)
        elif ndim == 2:
            self._write_2D_array(array_key, value, fh)
        elif ndim == 3:
            self._write_3D_array(array_key, value, fh)
        elif ndim == 4:
            self._write_4D_array(array_key, value, fh)
        else:
            raise ValueError('5D+ arrays not supported in sfe_cfg writer')

    def _write_1D_array(self, array_key: str, value: np.ndarray, fh: TextIOWrapper):
        for i in range(value.shape[0]):
            self._write_single_value(f'{array_key}({i})', value[i], fh)

    def _write_2D_array(self, array_key: str, value: np.ndarray, fh: TextIOWrapper):
        for i in range(value.shape[0]):
            for j in range(value.shape[1]):
                self._write_single_value(f'{array_key}({i},{j})', value[i, j], fh)

    def _write_3D_array(self, array_key: str, value: np.ndarray, fh: TextIOWrapper):
        for i in range(value.shape[0]):
            for j in range(value.shape[1]):
                for k in range(value.shape[2]):
                    self._write_single_value(f'{array_key}({i},{j},{k})', value[i, j, k], fh)

    def _write_4D_array(self, array_key: str, value: np.ndarray, fh: TextIOWrapper):
        for i in range(value.shape[0]):
            for j in range(value.shape[1]):
                for k in range(value.shape[2]):
                    for m in range(value.shape[2]):
                        self._write_single_value(f'{array_key}({i},{j},{k},{m})', value[i, j, k, m], fh)

    def _write_single_value(self, key: str, value, fh: TextIOWrapper):
        if type(value) == bool or type(value) == np.bool_:
            value = '.true.' if value else '.false.'
        fh.write(f'{key} = {value}\n')
