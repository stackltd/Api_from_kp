import datetime
import json
import logging
import sys
from pprint import pprint

import requests
import re

from prettytable import PrettyTable

from messages import text
from settings import token, query, RANDOM_MOVIE

HEADERS = {'X-API-KEY': token}
BASE_URL = 'https://api.kinopoisk.dev'
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
                'genres': 'жанр', 'status': 'статус', 'ageRating': 'ограничение по возрасту', 'facts': 'факты о фильме',
                'countries': 'страны', 'rating': 'рейтинг', 'votes': 'голоса', 'backdrop': 'фон', 'poster': 'постер',
                'seasonsInfo': 'сезонов', 'seriesLength': 'серий', 'totalSeriesLength': 'всего серий',
                'similarMovies': 'похожие фильмы', 'sequelsAndPrequels': 'сериалы и приквелы', 'persons': 'актеры и прочие'}


class Parser:
    """
    Класс, позволяющий создать json-файл, как результат парсинга стороннего API,
    а так же вывести информацию на экран.

    Attributes:
        count (int): позволяет вести подсчет количества вызовов метода
    """
    count = 0
    stop_parse = False
    requests_all = 0
    count_dupl = 0
    start = True
    stop = False
    dump_in = dict()
    dump_all = dict()
    all_keys = set()
    url_json = ''

    # @staticmethod
    def parse_json(self, endpoint, prnt, id_movie='') -> dict:
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
            if endpoint == '/v1.4/movie/random':
                querystring = query
            res: dict = requests.get(url=url, headers=HEADERS, params=querystring).json()
            if prnt:
                res_prn = json.dumps(res, indent=4, ensure_ascii=False)
                print(res_prn)
            if res.get('statusCode', '') == 403:
                # print(f'\033[031m{res["message"]}\033[039m')
                print(f'{res["message"]}', file=sys.stderr)
                self.stop_parse = True
                with open(file=self.url_json, mode='w', encoding='utf-8') as file:
                    json.dump(self.dump_in, file, indent=4, ensure_ascii=False)
                print(f'\n\033[095mКоличество записей в базе данных увеличено на {self.count}\n\033[039m')
        except Exception as ex:
            print(f'Ошибка парсинга {ex=}', file=sys.stderr)
            self.count += 1
        else:
            return res

    def make_json(self, id_movies=('',), prnt=False, pref='', parse_from_web=False, dump_from_web=None, from_list_id=False) -> bool:
        """
        Метод обновляет json-файл результатом парсинга API с разными эндпоинтами.
        :param prnt: параметр, разрешающий вывод результата в консоль.
        :param id_movie: кортеж с id, по которым производится поиск, если необходимо.
        """
        # Создаем объект из дампа.
        self.url_json = pref + "dumps/movies_info.json"
        if self.start:
            self.dump_all = self.get_json(pref=pref) if not parse_from_web else dump_from_web
            self.all_keys = set(self.dump_all.keys())
            with open(file=self.url_json, mode='r', encoding='utf-8') as file:
                self.dump_in: dict = json.load(file)
            self.start = False
        # Получаем json объект из стороннего API.
        for id_movie in id_movies:
            if self.stop_parse and from_list_id:
                break
            if id_movie in self.all_keys:
                # print(f'Этот фильм уже в базе: {id_movie=}')
                print(f'\033[032mЭтот фильм уже в базе:'
                      f' {self.dump_all[id_movie]["Общая информация о фильме"]["name"]}\033[039m')
                continue
            obj = self.parse_json(endpoint=INFO, id_movie=id_movie, prnt=prnt) if id_movie\
                else self.parse_json(endpoint=RANDOM_MOVIE, prnt=prnt)
            self.requests_all += 1
            id_movie_get = str(obj.get('id', 0))
            if id_movie_get in self.all_keys:
                self.count_dupl += 1
                print(f'\033[032m {self.count_dupl} ({self.requests_all}) Этот фильм уже в базе:'
                      f' {self.dump_all.get(id_movie_get, {}).get("Общая информация о фильме", {}).get("name", "")}\033[039m')
                if self.stop:
                    self.stop = False
                continue
            else:
                self.all_keys.add(id_movie_get)
            # Проверка соответствия типа полученного объекта obj и наличия в объекте ключа id.
            if isinstance(obj, dict) and (id_movie := obj.get('id', 0)):
                id_movie = str(id_movie)
                is_series = obj['isSeries']
                if not obj['name']:
                    name = obj['names'][0]['name']
                    obj['name'] = name
                dump_temp = dict.fromkeys(['Общая информация о фильме'], obj)
                dump_temp.update(
                    {'Информация о сезонах и эпизодах': self.parse_json(endpoint=ALL_SEAS_EPIS, id_movie=id_movie, prnt=prnt) if is_series else {}})
                if is_series:
                    self.requests_all += 1
                # проверяем, достигнут ли лимит запросов на данном этапе
                if dump_temp.get("Информация о сезонах и эпизодах").get("statusCode", '') == 403:
                    self.stop_parse = True
                    self.stop = True
                else:
                    dump_temp.update({'Отзывы зрителей': self.parse_json(endpoint=REVIEW, id_movie=id_movie, prnt=prnt)})
                    self.requests_all += 1
                    # проверяем, достигнут ли лимит запросов на данном этапе
                    if dump_temp.get("Отзывы зрителей").get("statusCode", '') == 403:
                        self.stop_parse = True
                        self.stop = True
                    else:
                        self.dump_in.update({id_movie: dump_temp})
                        self.count += 1
                        name_get_film = self.dump_in[id_movie]["Общая информация о фильме"]["name"]
                        print(self.count, f'({self.requests_all})', name_get_film)
            elif from_list_id:
                print('По этому id ничего не найдено!')
            else:
                print('По этому id ничего не найдено!')
                return False
        if self.stop or parse_from_web:
            with open(file=self.url_json, mode='w', encoding='utf-8') as file:
                json.dump(obj=self.dump_in, fp=file, indent=4, ensure_ascii=False)
            print(f'\n\033[095mКоличество записей в базе данных увеличено на {self.count}\n\033[039m')
        return True

    @staticmethod
    def get_json(prnt=False, id_movie='', url='dumps/movies_info.json', pref=''):
        """
        Метод создает json объект из файла. При необходимости можно вывести результат на экран.
        """
        with open(file=f'{pref}dumps/movies1_info.json', mode='r', encoding='utf-8') as file:
            dump_in: dict = json.load(file)
        with open(file=pref + url, mode='r', encoding='utf-8') as file:
            dump_in_2: dict = json.load(file)
        dump_in.update(dump_in_2)
        del dump_in_2
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
    def print_info(obj, prnt=True):
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

        def previews_info(prnt=prnt):
            if isinstance(info_preview, dict):
                obj = info_preview['docs']
            elif isinstance(info_preview, list):
                obj = info_preview
            else:
                obj = []
            previews = []
            for preview in obj:
                to_print = f"Ник: {preview.get('author')}, вывод: {preview.get('title')}, оценка: {preview.get('type')}"
                if prnt:
                    print('\n' + '-' * 10 + 'Отзывы' + '-' * 10)
                    print(to_print)
                    text = filter_text(patterns=PATTERNS, text=preview['review'])
                    print(text)
                    print('=' * 200 + '\n')
                previews.append({to_print: preview['review']})
            return previews

        def seasons_info(prnt=prnt):
            season_info = []
            if info_seasons:
                obj = info_seasons['docs']
                obj = sorted(obj, key=lambda x: int(x["number"]))
                for seasons in obj:
                    to_print = f"Сезон {seasons['number']}, число серий: {seasons.get('episodesCount')}"
                    string = '\n    '.join(
                        [f"{x['number']}.{x['name']} ({x['enName']}). {x['description']} {x.get('enDescription', '')}"
                         for x in seasons['episodes'] if x["description"] or x.get("enDescription")])
                    if string:
                        season_info.append({to_print: string})
                    if prnt and string:
                        print('\n' + '-' * 10 + 'Информация о сезонах' + '-' * 10)
                        print(to_print)
                        print(string)
            return season_info

        def movie_info(prnt=prnt):
            # sequelsAndPrequels
            all_info = dict()
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
                            if prnt:
                                string = filter_text(patterns=PATTERNS, text=string)
                        elif i == 'seasonsInfo':
                            string = len(info_movie.get("seasonsInfo"))
                        elif i == 'releaseYears':
                            string = ', '.join([f"начало: {x['start']}, конец: {x['end']}" for x in info_movie[i]])
                        elif i == 'persons':
                            string = '\n    '.join(
                                [f"{ind + 1}. {x['id']} {x['profession'][:-1]}: "
                                 f"{list(map(lambda x: x if x is not None else '', [x['enName']]))[0]}"
                                 f" ({list(map(lambda x: x if x is not None else '', [x['name']]))[0]}) {x['photo']}" for
                                 ind, x in enumerate(info_movie[i])])
                        elif i == 'similarMovies':
                            string = '\n    '.join(
                                [f"{x['name']} ({x['enName']}{x['alternativeName']}). id={x['id']} {x.get('poster').get('url')}" for x in info_movie[i]])
                        elif i == 'description':
                            string = filter_text(patterns=PATTERNS, text=info_movie[i])
                        elif i == 'sequelsAndPrequels':
                            string = ',\n    '.join([f"{x['name']} ({x['alternativeName']}), {x['type']}, id: {x['id']} {x.get('poster').get('url')}" for x in info_movie[i]])
                        elif i == 'seriesLength':
                            string = sum([x['episodesCount'] for x in info_movie.get('seasonsInfo')]) if info_movie.get('seasonsInfo') else ''
                        else:
                            string = f'{info_movie[i]}'
                        to_print = f"{KEYS_SEARCHE[i]}:\n    {string}"
                        all_info.update({KEYS_SEARCHE[i]: string})
                        if prnt:
                            print('-' * 10 + 'Общая информация' + '-' * 10)
                            print(to_print)
                except Exception as ex:
                    print(f'{ex=}')
                    raise
            return all_info

        all_info = movie_info()
        season_info = seasons_info()
        previews = previews_info()
        return all_info, previews, season_info

    @staticmethod
    def list_id(name):
        url = f'https://api.kinopoisk.dev/v1.3/movie?name={name}'
        res: dict = requests.get(url=url, headers=HEADERS).json()
        res_out = res.get('docs', {})
        list_out = [str(x['id']) for x in res_out]
        print(f'Найдено {len(res_out)} фильмов')
        return list_out

    def del_movie(self, movie_id) -> bool:
        for suffix in ('', '1'):
            with open(file=f'dumps/movies{suffix}_info.json', mode='r', encoding='utf-8') as file:
                dump: dict = json.load(file)
            keys = set(dump.keys())
            if movie_id in keys:
                dump.pop(movie_id, {})
                with open(file=f'dumps/movies{suffix}_info.json', mode='w', encoding='utf-8') as file:
                    json.dump(dump, file, indent=4, ensure_ascii=False)
                return True
        else:
            return False