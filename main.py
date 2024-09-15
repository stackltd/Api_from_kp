from utils import Parser
from deco import timer
from messages import *

parse = Parser()

@timer
def main() -> None:
    """
    Функция позволяет заполнять базу данных в виде json информацией о фильмах из API Кинопоиска,
    заполнять ее по известному id, а так же вывести информацию из json файла как в исходном виде, так и в кратком
    табличном формате.
    """
    while True:
        print('\nВыберите желаемый пункт меню:')
        ask_1 = input(main_menu)
        if ask_1 == '1':
            while True:
                try:
                    numb = int(input('Введите количество запросов к API\n'))
                    ask_2 = input(ask_print)
                    break
                except ValueError:
                    print('Ошибка ввода')
            [parse.make_json(prnt=ask_2 == '1') for _ in range(numb)]
            if parse.count:
                print(f'Количество записей в базе данных увеличено на {parse.count}\n')
                parse.count = 0
            else:
                print('База данных не была пополнена')
        elif ask_1 == '2':
            id_movies = []
            id_mov = input('Введите название, по которому будет произовдиться поиск.\n'
                           'Если нужно найти фильм по известному id, нашите звездочку после него\n')
            ask_2 = input(ask_print)
            if id_mov.endswith('*'):
                id_movies.append(id_mov[:-1])
            else:
                id_movies.extend(parse.list_id(id_mov))
            parse.make_json(id_movies=tuple(id_movies), prnt=ask_2=='1')
        elif ask_1 == '3':
            ask_2 = input('Будет выведена таблица с краткой информацией о фильмах.'
                          ' Если же хотите вывести все данные, введите 1, если только таблицу - любой символ\n')
            res = parse.get_json(prnt=ask_2 == '1')
            parse.print_table(obj=res)
            while True:
                ask_3 = input('Введите для сортировки по возрастанию: 1: по имени, 2: по году, 3: по типу, 4: по жанру,'
                              ' 5: по голосам, 6: по стране. '
                              'В обратном порядке - введите двойное число'
                              '\nДля поиска фильма и вывода в адаптированном виде введите id. В json-формате - напишите звездочку после id.'
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
                        obj = parse.get_json(prnt=False, id_movie=ask_3)
                        parse.print_info(obj=obj)
                        input('Нажмите ввод для вывода таблицы ')
                    parse.print_table(obj=res)
                else:
                    break
        elif ask_1 == '4':
            ask_2 = input('Введите id фильма, который нужно удалить\n')
            parse.del_movie(ask_2)
            res = parse.get_json()
            parse.print_table(obj=res)
        else:
            break


if __name__ == '__main__':
    main()
