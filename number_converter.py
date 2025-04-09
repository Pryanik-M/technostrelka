import pymorphy3
from typing import Tuple, List
import re


morph = pymorphy3.MorphAnalyzer()


number_dict = {
    'ноль': 0, 'один': 1, 'одна': 1, 'два': 2, 'две': 2, 'три': 3, 'четыре': 4,
    'пять': 5, 'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9, 'десять': 10,
    'одиннадцать': 11, 'двенадцать': 12, 'тринадцать': 13, 'четырнадцать': 14,
    'пятнадцать': 15, 'шестнадцать': 16, 'семнадцать': 17, 'восемнадцать': 18,
    'девятнадцать': 19, 'двадцать': 20, 'тридцать': 30, 'сорок': 40,
    'пятьдесят': 50, 'шестьдесят': 60, 'семьдесят': 70, 'восемьдесят': 80, 'девяносто': 90,
    'сто': 100, 'двести': 200, 'триста': 300, 'четыреста': 400, 'пятьсот': 500,
    'шестьсот': 600, 'семьсот': 700, 'восемьсот': 800, 'девятьсот': 900,
    'тысяча': 1000, 'тысячи': 1000, 'тысяч': 1000,
    'миллион': 1000000, 'миллиона': 1000000, 'миллионов': 1000000,
    'миллиард': 1000000000, 'миллиарда': 1000000000, 'миллиардов': 1000000000
}

multipliers = {'тысяча', 'тысячи', 'тысяч', 'миллион', 'миллиона', 'миллионов', 'миллиард', 'миллиарда', 'миллиардов'}


def tokenize_with_positions(txt: str) -> List[Tuple[str, int, int]]:
    words = []
    for match in re.finditer(r'\w+', txt):
        word = match.group()
        start = match.start()
        end = match.end()
        words.append((word, start, end))
    return words


def parse_number_sequence(normal_sequence: List[str]) -> int:
    total_value = 0
    current_group = 0
    current_multiplier = 1

    for word in normal_sequence:
        value = number_dict[word]
        if word in multipliers:
            if current_group == 0:
                current_group = 1
            total_value += current_group * value
            current_group = 0
            current_multiplier = 1
        else:
            current_group += value

    if current_group != 0:
        total_value += current_group * current_multiplier

    return total_value


def replace_numbers_with_digits(text: str) -> Tuple[str, List[Tuple[int, int, str]]]:
    tokens = tokenize_with_positions(text)
    replacements = []
    i = 0

    while i < len(tokens):
        word, start, end = tokens[i]
        word_lower = word.lower()
        parsed_word = morph.parse(word_lower)[0]
        normal_word = parsed_word.normal_form
        if normal_word in number_dict:
            number_sequence = [word]
            normal_sequence = [normal_word]
            sequence_start = start
            j = i + 1
            while j < len(tokens):
                next_word, next_start, next_end = tokens[j]
                next_word_lower = next_word.lower()
                next_parsed = morph.parse(next_word_lower)[0]
                next_normal = next_parsed.normal_form
                if next_normal in number_dict:
                    number_sequence.append(next_word)
                    normal_sequence.append(next_normal)
                    j += 1
                else:
                    break
            sequence_end = tokens[j-1][2] if j > i + 1 else end
            numeric_value = parse_number_sequence(normal_sequence)
            replacement = str(numeric_value)
            replacements.append((sequence_start, sequence_end, replacement))
            i = j
        else:
            i += 1

    final_text = text
    for start, end, replacement in sorted(replacements, key=lambda x: x[0], reverse=True):
        final_text = final_text[:start] + replacement + final_text[end:]

    return final_text, replacements