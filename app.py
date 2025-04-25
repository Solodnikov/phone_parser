import re
from pathlib import Path
from typing import Set

import click
from loguru import logger

logger.remove()
logger.add(
    "logs/logfile_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    level="INFO",
    retention="7 days",
    compression="zip",
)


class Extractor:
    PATTERN = re.compile(
        r'(?:(?:\+7|8)[\s\-\(\)]*)?'
        r'(?P<area>\d{3})[\s\-\(\)]*'
        r'(?P<part1>\d{3})[\s\-\.]*'
        r'(?P<part2>\d{2})[\s\-\.]*'
        r'(?P<part3>\d{2})'
    )

    def __init__(self, file_path: str) -> None:
        self._file_path = Path(file_path)
        self._found_numbers: Set[str] = set()

    def _load_text(self) -> str:
        """ return text from file
        """
        logger.info(f'чтение файла {self._file_path}')
        try:
            with open(self._file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logger.exception(
                f'отсуствует файл по адресу {self._file_path}')
        except Exception:
            logger.exception('ошибка при чтении файла')

    def extract(self) -> Set[str]:
        text = self._load_text()
        if not text:
            logger.warning("Пустой или нечитабельный файл")
            return set()
        logger.info(f'извлечение номеров из текста файла {self._file_path}')
        for match in self.PATTERN.finditer(text):
            formatted = self._format_number(match)
            if formatted and formatted not in self._found_numbers:
                self._found_numbers.add(formatted)

        return self._found_numbers

    def _format_number(self, match: re.Match) -> str:
        try:
            area = match.group("area")
            part1 = match.group("part1")
            part2 = match.group("part2")
            part3 = match.group("part3")
            return f"+7({area}){part1}-{part2}-{part3}"

        except Exception:
            logger.exception('ошибка при форматировании номера')

    def _result_message(self) -> str:
        return ('\n'.join(self._found_numbers) +
                '\n' + f'общее количество номеров: {len(self._found_numbers)}')

    def get_result_in_file(self):
        if self._found_numbers:
            logger.info(
                f'вывод номеров из текта файла {self._file_path} в файл')

            try:
                result_dir = Path('result')
                result_dir.mkdir(exist_ok=True)
                file_name = f'result_{self._file_path.name.split(".")[0]}.txt'
                full_file_path = result_dir / file_name
                with open(full_file_path, 'w',  encoding='utf-8') as file:
                    file.write(self._result_message())

            except Exception:
                logger.exception(
                    f'ошибка записи результатов файла {self._file_path.name}')
        else:
            print('отсутствуют номера для воспоизведения')

    def get_result_in_terminal(self):
        if self._found_numbers:
            logger.info(
                f'вывод номеров из текта файла {self._file_path} в терминал')
            print(self._result_message())
        else:
            print('отсутствуют номера для воспоизведения')


@click.command()
@click.option(
    '-f', '--file',
    is_flag=True,
    help='вывод результата в файл'
)
@click.argument('file_path', type=click.Path(exists=True))
def main(file_path: str, file: bool) -> None:
    extractor = Extractor(file_path)
    extractor.extract()

    if file:
        extractor.get_result_in_file()
    else:
        extractor.get_result_in_terminal()


if __name__ == "__main__":
    main()
