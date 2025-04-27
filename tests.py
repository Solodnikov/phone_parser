from collections import OrderedDict
from pathlib import Path

import pytest
from click.testing import CliRunner

from app import Extractor, main


FILE_NO_DATA = 'file_no_numbers.txt'
FILE_WITH_DATA = 'file_with_numbers.txt'


@pytest.fixture
def tmp_file_no_numbers(tmp_path: Path) -> Path:
    """Создаёт временный файл без номеров"""
    file_path = tmp_path / FILE_NO_DATA
    text = 'Текст без телефонов'
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(text)
    return file_path


@pytest.fixture
def tmp_file_with_numbers(tmp_path: Path) -> Path:
    """Создаёт временный файл c номерами"""
    file_path = tmp_path / FILE_WITH_DATA
    text = '''
    Позвоните мне по номеру +7 (999) 123-45-67 или 8 495 987 65 43.
    Также доступен 8(800)555.35.35
    '''
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(text)
    return file_path


def test_initialization(tmp_file_no_numbers):
    extractor = Extractor(tmp_file_no_numbers)
    assert extractor._file_path == Path(tmp_file_no_numbers)


def test_load_text_success(tmp_file_no_numbers):
    extractor = Extractor(tmp_file_no_numbers)
    assert extractor._load_text() == "Текст без телефонов"


def test_load_text_file_not_found():
    extractor = Extractor('nonexistent.txt')
    assert extractor._load_text() is None


def test_extract_numbers(tmp_file_with_numbers):
    extractor = Extractor(tmp_file_with_numbers)
    numbers = extractor.extract()
    sorted_list = [
        '+7(999)123-45-67',
        '+7(495)987-65-43',
        '+7(800)555-35-35']
    assert list(numbers.keys()) == sorted_list
    for i, value in enumerate(numbers.keys()):
        assert sorted_list[i] == value


def test_extract_empty_file(tmp_file_no_numbers):
    extractor = Extractor(tmp_file_no_numbers)
    numbers = extractor.extract()
    assert numbers == OrderedDict()


def test_get_result_in_file(tmp_file_with_numbers):
    extractor = Extractor(tmp_file_with_numbers)
    extractor.extract()
    extractor.get_result_in_file()

    result_dir = Path('results')
    result_files = list(result_dir.glob(f'result_{FILE_WITH_DATA}'))
    assert len(result_files) == 1

    try:
        content = result_files[0].read_text(encoding='utf-8')
        assert "+7(999)123-45-67" in content
    finally:
        result_files[0].unlink()


def test_get_result_in_terminal(tmp_file_with_numbers, capsys):
    extractor = Extractor(tmp_file_with_numbers)
    extractor.extract()
    extractor.get_result_in_terminal()

    captured = capsys.readouterr()
    assert "+7(999)123-45-67" in captured.out


def test_get_result_in_terminal_empty(tmp_file_no_numbers, capsys):
    extractor = Extractor(tmp_file_no_numbers)
    extractor.extract()
    extractor.get_result_in_terminal()

    captured = capsys.readouterr()
    assert "отсутствуют номера" in captured.out


# CLI тесты

def test_main_cli_terminal(tmp_file_with_numbers):
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_file_with_numbers)])
    assert result.exit_code == 0
    assert "+7(999)123-45-67" in result.output


def test_main_cli_file(tmp_file_with_numbers):
    result_files = []
    try:
        runner = CliRunner()
        result = runner.invoke(main, ['--file', str(tmp_file_with_numbers)])
        assert result.exit_code == 0

        result_dir = Path('results')
        result_files = list(result_dir.glob(f'result_{FILE_WITH_DATA}'))
        assert len(result_files) == 1

    finally:
        for file in result_files:
            file.unlink()
