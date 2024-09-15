import os
import re
import sys

from utils import Parser
from deco import timer
from messages import *

parse = Parser()

def zero():
    parse.count = 0
    parse.requests_all = 0
    parse.count_dupl = 0
    parse.stop = False
    parse.start = True
    del parse.dump_in

@timer
def main() -> None:
    """
    Функция позволяет заполнять базу данных в виде json информацией о фильмах из API Кинопоиска,
    заполнять ее по-известному id, а так же вывести информацию из json файла как в исходном виде, так и в кратком
    табличном формате.
    """
    while True:
        print('\nВыберите желаемый пункт меню:')
        ask_1 = input(main_menu)
        if ask_1 == '1':
            while True:
                try:
                    numb = int(input('Введите количество записей, которые нужно добавить в базу\n'))
                    if numb < 0:
                        raise ValueError
                    ask_2 = input(ask_print)
                    break
                except ValueError as ex:
                    print('Ошибка ввода', file=sys.stderr)
            print('in progress...')

            while parse.count != numb and not parse.stop_parse:
                try:
                    if numb - parse.count <= 1:
                        parse.stop = True
                    parse.make_json(prnt=ask_2 == '1')
                except Exception as ex:
                    print(f'Произошла ошибка: {ex = }', file=sys.stderr)
                    # raise
                    # break
            if parse.count:
                print(f'Использовано запросов: {parse.requests_all}')
                perc_dupl = round((parse.count_dupl / (parse.count_dupl + parse.count)) * 100)
                print(f'Дублей: {parse.count_dupl} ({perc_dupl} %)')
                zero()
            else:
                print('База данных не была пополнена')
        elif ask_1 == '2':
            id_movies = []
            id_mov = input('Введите название, по которому будет производиться поиск.\n'
                           'Если нужно найти фильмы по известному id, составьте список id через пробел, с диапазоном'
                           ' через дефис, и/или перечислением\n')
            ask_2 = input(ask_print)
            pattern = r'[^a-zA-Zа-яА-Я]+'
            res = re.fullmatch(pattern, id_mov)
            if res:
                info = id_mov.split()
                info = [[str(y) for y in range(int(x.split('-')[0]), int(x.split('-')[1]) + 1)]
                        if '-' in x else x
                        for x in info]
                for x in info:
                    if isinstance(x, list):
                        id_movies.extend(x)
                    else:
                        id_movies.append(x)
            else:
                id_movies.extend(parse.list_id(id_mov))
            parse.stop =True
            parse.make_json(id_movies=tuple(id_movies), prnt=ask_2 == '1', from_list_id=True)
            zero()
        elif ask_1 == '3':
            ask_2 = input('Будет выведена таблица с краткой информацией о фильмах.'
                          ' Если же хотите вывести все данные, введите 1, если только таблицу - любой символ\n')
            res = parse.get_json(prnt=ask_2 == '1')
            parse.print_table(obj=res)
            while True:
                ask_3 = input('Введите для сортировки по возрастанию: 1: по имени, 2: по году, 3: по типу, 4: по жанру,'
                              ' 5: по голосам, 6: по стране. '
                              'В обратном порядке - введите двойное число'
                              '\nДля поиска фильма и вывода в адаптированном виде введите id. В json-формате - '
                              'напишите звездочку после id.'
                              '\nДля удаления фильма из базы введите его id и напишите знак минус (-) после него'
                              '\nВыход в основное меню - нажмите энтер.\n')
                if ask_3 in ('1', '2', '3', '4', '5', '6', '11', '22', '33', '44', '55', '66'):
                    field_sort = ask_3 if len(ask_3) == 1 else ask_3[:1]
                    is_reverse = len(ask_3) == 2
                    parse.print_table(obj=res, field_sort=field_sort, is_reverse=is_reverse)
                elif ask_3 != '':
                    if ask_3.endswith('*'):
                        parse.get_json(prnt=True, id_movie=ask_3[:-1])
                        input('Нажмите ввод для вывода таблицы ')
                    elif ask_3.endswith('-'):
                        parse.del_movie(ask_3[:-1])
                        res = parse.get_json()
                        parse.print_table(obj=res)
                    else:
                        obj = parse.get_json(id_movie=ask_3)
                        parse.print_info(obj=obj)
                        input('Нажмите ввод для вывода таблицы ')
                    parse.print_table(obj=res)
                else:
                    break
        elif ask_1 == '4':
            ask_2 = input('\nДля поиска фильма и вывода в адаптированном виде введите id. В json-формате - '
                          'напишите звездочку после id.\n')
            if ask_2.endswith('*'):
                parse.get_json(prnt=True, id_movie=ask_2[:-1])
            else:
                obj = parse.get_json(id_movie=ask_2)
                parse.print_info(obj=obj)
        elif ask_1 == '5':
            ask_2 = input('Введите id фильма, который нужно удалить\n')
            res = parse.del_movie(ask_2)
            if res:
                print(f'Данные с id {ask_2} удалены')
            else:
                print(f'Данные с id {ask_2} не найдены')
        else:
            break


if __name__ == '__main__':
    print(os.getenv('PYTHONPATH'))
    main()
