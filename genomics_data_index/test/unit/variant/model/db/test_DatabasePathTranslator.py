import pytest

from tempfile import TemporaryDirectory
from pathlib import Path
from os import mkdir

from genomics_data_index.storage.model.db.DatabasePathTranslator import DatabasePathTranslator


def test_translate_from_database():
    with TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        expected1 = tmp_dir / 'file1'
        expected2 = tmp_dir / 'dir' / 'file2'
        expected3 = tmp_dir / 'dir' / 'subdir' / 'file3.txt'

        # Create files
        mkdir(tmp_dir / 'dir')
        mkdir(tmp_dir / 'dir' / 'subdir')
        open(expected1, 'w').close()
        open(expected2, 'w').close()
        open(expected3, 'w').close()

        dpt = DatabasePathTranslator(tmp_dir)

        actual_file = dpt.from_database('file1')
        assert actual_file == expected1

        actual_file = dpt.from_database('dir/file2')
        assert actual_file == expected2

        actual_file = dpt.from_database('dir/subdir/file3.txt')
        assert actual_file == expected3


def test_translate_from_database_fail():
    with TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)

        dpt = DatabasePathTranslator(tmp_dir)

        with pytest.raises(Exception) as execinfo:
            dpt.from_database('file1')
        assert 'does not exist for relative path' in str(execinfo.value)
