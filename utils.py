import json
import requests
import re

from prettytable import PrettyTable

from messages import text
from settings import token

HEADERS = {'X-API-KEY': token}
BASE_URL = 'https://api.kinopoisk.dev'
RANDOM_MOVIE = '/v1/movie/random'
INFO = '/v1.3/movie/'
ALL_SEAS_EPIS = '/v1/season'
REVIEW = '/v1/review'

FIELDS = {'1': 'name', '2': 'year', '3': 'type', '4': 'genres', '5': 'votes', '6': 'countries'}

PATT1 = r"""[^<>a-zA-Z;\|_\{\}\[\]\\"=!@%&^*()\+]+"""
PATT2 = r"""/+[0-9]+/+"""
PATT3 = r"""&#\d+|&?#\d+"""
PATT4 = r"""[^/]"""
PATT5 = r"""\.,"""
PATTERNS = [PATT1, PATT2, PATT3, PATT4, PATT5]

KEYS_SEARCHE = {'name': 'название', 'description': 'описание', 'type': 'тип', 'year': 'год', 'releaseYears': 'период',
                'genres': 'жанр', 'status': 'статус', 'ageRating': 'ограничение по возрасту', 'facts': 'факты о фильмы',
                'countries': 'страны', 'rating': 'рейтинг', 'votes': 'голоса', 'backdrop': 'фон', 'poster': 'постер',
                'seasonsInfo': 'сезоны', 'seriesLength': 'серий', 'totalSeriesLength': 'всего серий',
                'similarMovies': 'похожие фильмы', 'sequelsAndPrequels': 'сериалы и приквелы', 'persons': 'актеры и прочие'}

class Parser:
    """
    Класс, позволяющий создать json-файл, как результат парсинга стороннего API,
    а так же вывести информацию на экран.

    Attributes:
        count (int): позволяет вести подсчет количества вызовов метода
    """
    count = 0

    @staticmethod
    def parse_json(endpoint, prnt, id_movie='') -> dict:
        """
        Метод возвращает json-объект, как результат парсинга стороннего API.
        :param endpoint: эндпоинт, по которому производится запрос API.
        :param prnt: ключ id, по которому производится поиск если необходимо.
        :param id_movie: параметр, разрешающий вывод результата в консоль.
        """
        try:
            # Формирование запроса по входящим данным.
            third_param = id_movie if endpoint in ('/v1.3/movie/', '/v1/movie/') else ''
            url = ''.join([BASE_URL, endpoint, third_param])
            querystring = {'movieId': id_movie} if id_movie else {}
            res: dict = requests.get(url=url, headers=HEADERS, params=querystring).json()
            if prnt:
                res_prn = json.dumps(res, indent=4, ensure_ascii=False)
                print(res_prn)
        except Exception as ex:
            print(f'Ошибка парсинга {ex=}')
        else:
            return res

    def make_json(self, id_movies=('',), prnt=False) -> None:
        """
        Метод обновляет json-файл результатом парсинга API с разными эндпоинтами.
        :param prnt: параметр, разрешающий вывод результата в консоль.
        :param id_movie: кортеж с id, по которым производится поиск, если необходимо.
        """
        # Создаем объект из дампа.
        with open('dumps/movies_info.json', 'r', encoding='utf-8') as file:
            dump_in: dict = json.load(file)
        # Получаем json объект из стороннего API.
        for id_movie in id_movies:
            if id_movie in dump_in.keys():
                continue
            obj = self.parse_json(endpoint=INFO, id_movie=id_movie, prnt=prnt) if id_movie\
                else self.parse_json(endpoint=RANDOM_MOVIE, prnt=prnt)
            # Проверка соответствия типа полученного объекта obj и наличия в объекте ключа id.
            if isinstance(obj, dict) and (id_movie := obj.get('id', 0)):
                id_movie = str(id_movie)
                isSeries = obj['isSeries']
                dump_temp = dict.fromkeys(['Общая информация о фильме'], obj)
                dump_temp.update(
                    {'Информация о сезонах и эпизодах': self.parse_json(endpoint=ALL_SEAS_EPIS, id_movie=id_movie, prnt=prnt) if isSeries else {}})
                dump_temp.update({'Отзывы зрителей': self.parse_json(endpoint=REVIEW, id_movie=id_movie, prnt=prnt)})
                dump_in.update({id_movie: dump_temp})
                with open(f'dumps/movies_info.json', 'w', encoding='utf-8') as file:
                    json.dump(dump_in, file, indent=4, ensure_ascii=False)
                self.count += 1
            else:
                print('По этому id ничего не найдено!')

    @staticmethod
    def get_json(prnt=False, id_movie=''):
        """
        Метод создает json объект из файла. При необходимости выводит результат на экран.
        """
        with open('dumps/movies_info.json', 'r', encoding='utf-8') as file:
            dump_in: dict = json.load(file)
            if id_movie:
                dump_in = dump_in.get(id_movie, {'message': 'По этому id ничего не найдено!'})
            if prnt:
                res: str = json.dumps(dump_in, indent=4, ensure_ascii=False)
                print(res)
        return dump_in

    @staticmethod
    def print_table(obj, field_sort=None, is_reverse=False) -> None:
        """
        Метод формирует поля для вывода информации в табличном варианте.
        """
        # Сортировка словаря по значениям полей
        if field_sort:
            obj = {x: obj[x] for x in sorted(obj.keys(), key=lambda a:
            int(obj[a][text].get(FIELDS[field_sort]).get('kp', 0)) if field_sort in ('5', '55') else str(
                obj[a][text].get(FIELDS[field_sort], '')), reverse=is_reverse
                                             )}
        # В данном списке формируются поля для таблицы. В случае длинных текстов, они обрезаются.
        list_mov = [[ind + 1,
                     key,
                     list(map(lambda x: x[:25] + '..' if len(x) > 25 else x, [str(obj[key][text]['name'])]))[0],
                     obj[key][text]['year'],
                     obj[key][text]['type'][:12],
                     ','.join(list(map(lambda x: x['name'][:3] if len(obj[key][text]['genres']) >= 3 else x['name'],
                                       obj[key][text]['genres']))),
                     obj[key][text]['votes'].get('kp', '-'),
                     list(map(lambda x: x[:70] + '..' if len(x) > 75 else x,
                              [str(obj[key][text].get('description', ''))]))[0].replace('\n', ''),
                     ','.join(list(map(lambda x: x['name'] if len(obj[key][text]['countries']) == 1 else x['name'][:3],
                                       obj[key][text]['countries'])))[:28]]
                    for ind, key in enumerate(obj.keys())]
        my_table = PrettyTable()
        my_table.field_names = ["id", "mov_id", "name", "year", "тип", "жанр", "голосов", "описание", "страна"]
        my_table.add_rows(list_mov)
        print(my_table)


    @staticmethod
    def print_info(obj):
        info_movie = obj.get('Общая информация о фильме')
        info_seasons = obj.get('Информация о сезонах и эпизодах')
        info_preview = obj.get('Отзывы зрителей')
        if not info_movie:
            print('Нет данных по этому id')
            return

        def filter_text(patterns, text):
            def parse_html(text, pattern, replace=False, repl=''):
                res = re.findall(pattern, text)
                if replace:
                    text_out = re.sub(pattern, repl, text)
                else:
                    text_out = ' '.join(''.join(res).split())
                return ' '.join(''.join(text_out).split())

            for ind, patt in enumerate(patterns):
                replace = ind in (1, 2, 4)
                if ind == 4:
                    repl = '.'
                else:
                    repl = ''
                text = parse_html(text=text, pattern=patt, replace=replace, repl=repl)
            return text

        def previews_info():
            print('\n' + '-' * 10 + 'Отзывы' + '-' * 10)
            if info_preview:
                obj = info_preview['docs']
                for preview in obj:
                    print(f"Ник: {preview.get('author')}, вывод: {preview.get('title')}, оценка: {preview.get('type')}")
                    text = filter_text(patterns=PATTERNS, text=preview['review'])
                    print(text)
                    print('=' * 200 + '\n')

        def seasons_info():
            print('\n' + '-' * 10 + 'Информация о сезонах' + '-' * 10)
            if info_seasons:
                obj = info_seasons['docs']
                for seasons in obj[::-1]:
                    print(f"Сезон {seasons['number']}, число серий: {seasons.get('episodesCount')}")
                    string = '\n    '.join(
                        [f"{x['number']}.{x['name']} ({x['enName']}). {x['description']}" for x in seasons['episodes']])
                    print(string)

        def movie_info():
            print('-' * 10 + 'Общая информация' + '-' * 10)

            # sequelsAndPrequels

            for i in KEYS_SEARCHE:
                try:
                    if info_movie.get(i, {}):
                        if i == 'rating':
                            string = info_movie[i]['kp']
                        elif i == 'votes':
                            string = info_movie[i]['kp']
                        elif i in ('poster', 'backdrop'):
                            string = info_movie[i]['url']
                        elif i in ('facts', 'genres', 'countries') and info_movie[i] is not None:
                            if i == 'facts':
                                key = 'value'
                            else:
                                key = 'name'
                            string = ', '.join([x[key] for x in info_movie[i]])
                            string = filter_text(patterns=PATTERNS, text=string)
                        elif i == 'seasonsInfo':
                            string = ', '.join(
                                [f"номер: {x['number']} (серий: {x['episodesCount']})" for x in info_movie[i]])
                        elif i == 'releaseYears':
                            string = ', '.join([f"начало: {x['start']}, конец: {x['end']}" for x in info_movie[i]])
                        elif i == 'persons':
                            string = '\n    '.join(
                                [f"{ind + 1}. {x['profession'][:-1]}: {x['enName']} ({x['name']}) {x['photo']}" for
                                 ind, x in enumerate(info_movie[i])])
                        elif i == 'similarMovies':
                            string = '\n    '.join(
                                [f"{x['name']} ({x['enName']}{x['alternativeName']}). id={x['id']} {x.get('poster').get('url')}" for x in info_movie[i]])
                        elif i == 'description':
                            string = filter_text(patterns=PATTERNS, text=info_movie[i])
                        elif i == 'sequelsAndPrequels':
                            string = ',\n    '.join([f"{x['name']} ({x['alternativeName']}), {x['type']}, id: {x['id']} {x.get('poster').get('url')}" for x in info_movie[i]])
                        else:
                            string = info_movie[i]
                        print(f"{KEYS_SEARCHE[i]}:\n    {string}")
                except Exception as ex:
                    print(f'{ex=}')
                    raise

        movie_info()
        input('Нажмите ввод для вывода информации о сезонах')
        print()
        seasons_info()
        input('Нажмите ввод для вывода отзывов')
        print()
        previews_info()

    @staticmethod
    def list_id(name):
        url = f'https://api.kinopoisk.dev/v1.3/movie?name={name}'
        res: dict = requests.get(url=url, headers=HEADERS).json()
        res_out = res['docs']
        list_out = [str(x['id']) for x in res_out]
        print(f'Найдено {len(res_out)} фильмов')
        return list_out


    @staticmethod
    def del_movie(movie_id):
        with open('dumps/movies_info.json', 'r', encoding='utf-8') as file:
            dump_in: dict = json.load(file)
        dump_in.pop(movie_id, {})
        with open(f'dumps/movies_info.json', 'w', encoding='utf-8') as file:
            json.dump(dump_in, file, indent=4, ensure_ascii=False)
