import json
import os
import sys

import requests
import re

from settings import token, query, RANDOM_MOVIE
from site_app.models import get_all_mov_id, get_long_info, json_to_sql, delete

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
    dump_in = {}
    all_keys = set()

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
                print(f'{res["message"]}', file=sys.stderr)
                self.stop_parse = True
                # записываем в бд вычисленный dump_in
                json_to_sql(json_info=self.dump_in)
                print(f'\033[095mКоличество записей в базе данных увеличено на {self.count}\033[039m')
        except Exception as ex:
            # raise
            print(f'Ошибка парсинга {ex=}', file=sys.stderr)
            self.count += 1
        else:
            return res

    def make_json(self, id_movies=('',), prnt=False, parse_from_web=False, from_list_id=False) -> bool:
        """
        Метод обновляет sql базу результатом парсинга API с разными эндпоинтами.
        :param prnt: параметр, разрешающий вывод результата в консоль.
        :param id_movie: кортеж с id, по которым производится поиск, если необходимо.
        """
        # Создаем объект из дампа.
        if self.start:
            self.all_keys = get_all_mov_id()
            self.dump_in = {}
            self.start = False
        # Получаем json объект из стороннего API.
        for id_movie in id_movies:
            if self.stop_parse and from_list_id:
                break
            if id_movie in self.all_keys:
                print(f'\033[032mЭтот фильм уже в базе:'
                      f' {get_long_info(id_movie=id_movie)["Общая информация о фильме"]["name"]}\033[039m')
                continue
            obj = self.parse_json(endpoint=INFO, id_movie=id_movie, prnt=prnt) if id_movie\
                else self.parse_json(endpoint=RANDOM_MOVIE, prnt=prnt)
            self.requests_all += 1
            if obj is None:
                return False
            id_movie_get = str(obj.get('id', 0))
            if id_movie_get in self.all_keys:
                self.count_dupl += 1
                print(f'\033[032m {self.count_dupl} ({self.requests_all}) Этот фильм уже в базе:'
                      f' {get_long_info(id_movie=id_movie_get)["Общая информация о фильме"]["name"]}\033[039m')
                if self.stop:
                    self.stop = False
                continue
            else:
                self.all_keys.add(id_movie_get)
            # Проверка соответствия типа полученного объекта obj и наличия в объекте ключа id.
            # print(f"{obj = }")
            if isinstance(obj, dict) and (id_movie := obj.get('id', 0)):
                id_movie = str(id_movie)
                is_series = obj['isSeries']
                if not obj['name']:
                    try:
                        name = obj['names'][0]['name']
                        obj['name'] = name
                    except IndexError:
                        obj['name'] = "неизвестно"
                dump_temp = dict.fromkeys(['Общая информация о фильме'], obj)
                dump_temp.update(
                    {'Информация о сезонах и эпизодах': self.parse_json(endpoint=ALL_SEAS_EPIS, id_movie=id_movie, prnt=prnt) if is_series else {}})
                if is_series:
                    self.requests_all += 1
                # проверяем, достигнут ли лимит запросов на данном этапе
                try:
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
                except AttributeError as ex:
                    print(f"AttributeError {ex = }")
                    return False
            elif from_list_id:
                print('По этому id ничего не найдено!')
            else:
                print('По этому id ничего не найдено!')
                return False
        if self.stop or parse_from_web:
            json_to_sql(json_info=self.dump_in)
            print(f'\033[095mКоличество записей в базе данных увеличено на {self.count}\033[039m')
        return True

    @staticmethod
    def get_json(id_movie, prnt=False):
        """
        Метод получает json объект из базы sql. При необходимости можно вывести результат на экран.
        """
        res = get_long_info(id_movie=id_movie)
        dump_in = res if res else {'message': 'По этому id ничего не найдено!'}
        if prnt:
            res: str = json.dumps(dump_in, indent=4, ensure_ascii=False)
            print(res)
        return dump_in


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

    @staticmethod
    def del_movie(movie_id) -> bool:
        film_is_exist = get_long_info(id_movie=movie_id)
        if film_is_exist:
            delete(id_movie=movie_id)
            return True

