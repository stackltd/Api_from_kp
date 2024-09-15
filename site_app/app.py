import json
import os
import random
import logging

from flask import Flask, request, render_template, redirect
from utils import Parser

from  messages import error

app = Flask(__name__)

formatter  = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%d.%m.%Y %H:%M:%S %A")
logger = logging.getLogger('werkzeug') # grabs underlying WSGI logger
handler = logging.FileHandler('test.log') # creates handler for the log file
handler_2 = logging.StreamHandler()
handler.setFormatter(formatter)
handler_2.setFormatter(formatter)
handler_2.setLevel(logging.ERROR)
logger.addHandler(handler) # adds handler to the werkzeug WSGI logger
logger.addHandler(handler_2)

movie_list = []


@app.route('/', methods=['POST', 'GET'])
def index():
    get_form = request.form
    form_values = set(get_form.values())
    form_keys = set(get_form.keys())
    global movie_list
    field_sort = {'название': 2, 'id': 0, 'страна': 3, 'год': 4, 'жанр': 5, 'голоса': 7}
    # print(list(get_form.items()))

    list_img = []
    for file in os.listdir('./static/img'):
        if file.startswith('collage'):
            list_img.append(file)
    image = random.choice(list_img)
    image_link = f'../static/img/{image}'

    # создаем фильм-лист, если не выбраны опции сортировки
    fields = set(field_sort)
    fields.update(countries_all)
    if not form_values.intersection(fields):
        movie_list = []
        for movie in dump_in.values():
            list_of_dict = movie["Общая информация о фильме"]
            genres_list = list_of_dict["genres"]
            genres_set = {genre["name"] for genre in genres_list}
            if form_keys <= genres_set:
                name_movie = str(list_of_dict['name'])
                countries = ', '.join(country['name'] for country in list_of_dict['countries'])
                year = str(list_of_dict['year']) if list_of_dict['year'] else '0'
                genres_movie = ', '.join(country['name'] for country in list_of_dict['genres'])
                print(genres_movie)
                id_movie = list_of_dict["id"]
                votes = str(list_of_dict["votes"].get('kp', 0))
                all_info = [str(id_movie), f'<span>{str(id_movie)}</span>', name_movie, countries, year, genres_movie,
                            f'<span>{votes}</span>', votes]
                movie_list.append(all_info)
    # print(movie_list[0])
    # ['1227993', '<span>1227993</span>', 'Водоворот', 'Россия', '2020', 'триллер, драма, детектив, криминал', '<span>151311</span>', '151311']
    # сортировка уже заготовленного списка фильмов
    # print(movie_list)
    if get_form.get('field', '') in field_sort:
        value = get_form['field']
        is_reverse = get_form.get('revers', '') == 'on'
        if value == 'голоса':
            is_reverse = not is_reverse
        ind = field_sort[value]
        movie_list = sorted(movie_list, key=lambda x: x[ind] if ind not in (0, 4, 7) else int(x[ind]),
                            reverse=is_reverse)
    elif get_form.get('field', '') in countries_all:
        value = get_form['field']
        movie_list = [movie for movie in movie_list if value in movie[3].split(', ')]

    movies = {(ind + 1, movie[0]): '. '.join(movie[1:-1]) for ind, movie in enumerate(movie_list)}

    return render_template('index.html', genres=list(genres), movies=movies, image=image_link,
                           field_sort=list(field_sort.keys())[1:], countries_all=countries_all)


@app.route('/film/<int:mov_id>')
def page(mov_id: int):
    global dump_in
    if mov_id == 0:
        with open(file='../dumps/movies_info.json', mode='r', encoding='utf-8') as file:
            dump_in_2 = json.load(file)
            dump_in.update(dump_in_2)
            return redirect(location=f"http://127.0.0.2/")
        # return (f'<p style="width: 100%; min-height: 50vh; padding-top: 50vh; font-size: 30px; text-align: center;'
        #         f' background-color: #a7b9dc;">Информация обновлена</p>')
    elif mov_id == 1:
        dump_in = Parser().get_json(pref='../')
        return redirect(location=f"http://127.0.0.2/")
        # return (f'<p style="width: 100%; min-height: 50vh; padding-top: 50vh; font-size: 30px; text-align: center;'
        #         f' background-color: #a7b9dc;">Информация обновлена</p>')

    all_info = dump_in.get(str(mov_id), {})
    if not all_info:
        result = Parser().make_json(id_movies=tuple((str(mov_id),)), pref='../', parse_from_web=True,
                                    dump_from_web=dump_in)
        if not result:
            return error, 404
        else:
            with open(file='../dumps/movies_info.json', mode='r', encoding='utf-8') as file:
                dump_in_2 = json.load(file)
            dump_in.update(dump_in_2)
            all_info = dump_in.get(str(mov_id), {})
    common_info = all_info["Общая информация о фильме"]
    name = common_info["name"]
    description = common_info["description"] if common_info["description"] is not None else name
    information = Parser().print_info(obj=all_info, prnt=False)
    info_base = information[0]
    info_block = [(point, info_base.get(point, '')) for point in ("название", "год", "тип", "жанр", "страны",
                                                                  "ограничение по возрасту", "рейтинг", "голоса",
                                                                  "серий", "сезонов",
                                                                  "факты о фильме") if information[0].get(point, '')]

    similar = sim_seq_movie(key="similarMovies", common_info=common_info)
    sequels = sim_seq_movie(key="sequelsAndPrequels", common_info=common_info)

    actors_list = []
    # print(f'{information[0]=}')
    actors_info = information[0].get('актеры и прочие', '').split('\n    ')
    # print(f'{actors_info=}')
    for point in actors_info:
        if point:
            actors = []
            list_point = point.split()
            # print(f'{list_point=}')
            actors.extend([list_point[0], list_point[1], list_point[-1], ' '.join(list_point[2:-1])])
            actors_list.append(actors)
        else:
            actors_list = [['', '', '', 'Нет данных']]

    trailer = common_info.get("videos", {})
    trailer = trailer.get("trailers", []) if trailer else []

    seasons_info = information[2]
    seasons = []
    # print(seasons_info)
    for info_seas in seasons_info:
        key = list(info_seas.keys())[0]
        values = list(info_seas.values())[0].split('\n    ')
        title_content = []
        for value in values:
            index = value.index(')')
            title_series = value[:index + 2]
            content_series = value[index + 3:]
            series = (title_series, content_series)
            title_content.append(series)
        seasons.append((key, title_content))

    preview_info = information[1]
    previews = []
    for info_seas in preview_info:
        key = list(info_seas.keys())[0]
        values = list(info_seas.values())[0].split('\n')
        previews.append((key, values))

    try:
        poster = common_info["poster"]["url"]
        backdrop = common_info["backdrop"]["url"]
        images = [backdrop, poster]
        random.shuffle(images)
    except TypeError:
        images = ['', '']
    return render_template('page.html', images=images, name=name, description=description, info_block=info_block,
                           actors_list=actors_list, similar=similar, sequels=sequels, trailer=trailer,
                           seasons=seasons, previews=previews)


def sim_seq_movie(key, common_info):
    out_list = []
    for movie_info in common_info.get(key, {}):
        names = r"/".join(
            map(lambda x: x if x else '', [movie_info['name'], movie_info['enName'], movie_info['alternativeName']]))
        mov_id = movie_info["id"]
        url = '' if dump_in.get(str(mov_id), {}) else "https://www.kinopoisk.ru/film/"
        names = fr"""<a href="{url}{mov_id}" target="_blank">{names}</a>"""
        out_list.append(names)
    return out_list


def points(key):
    list_points = []
    for movie in dump_in.values():
        list_of_dict = movie["Общая информация о фильме"][key]
        points_list = [genre["name"] for genre in list_of_dict]
        list_points.extend(points_list)
    else:
        list_points = sorted(set(list_points))
    return list_points


logger.debug('Запуск сайта')

dump_in = Parser().get_json(pref='../')

genres = points("genres")
countries_all = points("countries")

if __name__ == "__main__":
    app.run(host='127.0.0.2', port=80, debug=True)
