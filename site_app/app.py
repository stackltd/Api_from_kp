import os
import random
import logging

from flask import Flask, request, render_template, redirect
from utils import Parser

from models import get_info, get_field, get_long_info

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


def sim_seq_movie(key, common_info):
    out_list = []
    for movie_info in common_info.get(key, {}):
        names = r"/".join(
            map(lambda x: x if x else '', [movie_info['name'], movie_info['enName'], movie_info['alternativeName']]))
        mov_id = movie_info["id"]
        res = get_long_info(id_movie=mov_id)
        if res:
            print(f"фильма с {mov_id = } есть в базе")
        else:
            res = Parser().make_json(id_movies=tuple((str(mov_id),)), parse_from_web=True)
        url = '' if res else "https://www.kinopoisk.ru/film/"
        names = fr"""<a href="{url}{mov_id}" target="_blank">{names}</a>"""
        out_list.append(names)
    return out_list


def points(field, genres=("", )):
    list_points = []
    result = get_field(field=field, genres=genres)
    for fields in result:
        points_list = fields[0].split(", ")
        list_points.extend(points_list)
    else:
        list_points = sorted(set(list_points))
    return list_points


@app.route('/', methods=['POST', 'GET'])
def index():
    genres = points("genres")
    countries_all = points("countries")

    get_form = request.form
    form_values = set(get_form.values())
    form_keys = set(get_form.keys())
    global movie_list
    field_sort = {'название': 2, 'id': 0, 'страна': 3, 'год': 4, 'жанр': 5, 'голоса': 7}

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
        result = get_info(genres=form_keys) if form_keys else get_info()
        countries_all = points(field="countries", genres=form_keys) if form_keys else points(field="countries")
        for movie in result:
            name_movie = movie.name
            countries = movie.countries
            year = str(movie.year)
            genres_movie = movie.genres
            id_movie = str(movie.id_movie)
            votes = str(movie.votes)
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
    all_info = get_long_info(id_movie=mov_id)
    if not all_info:
        result = Parser().make_json(id_movies=tuple((str(mov_id),)), parse_from_web=True)
        if not result:
            return redirect(f"https://www.kinopoisk.ru/film/{mov_id}")
        all_info = get_long_info(id_movie=mov_id)

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
    actors_info = information[0].get('актеры и прочие', '').split('\n    ')
    for point in actors_info:
        if point:
            actors = []
            list_point = point.split()
            actors.extend([list_point[0], list_point[1], list_point[-1], ' '.join(list_point[2:-1])])
            actors_list.append(actors)
        else:
            actors_list = [['', '', '', 'Нет данных']]

    trailer = common_info.get("videos", {})
    trailer = trailer.get("trailers", []) if trailer else []

    seasons_info = information[2]
    seasons = []
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



logger.info('Запуск сайта')


if __name__ == "__main__":
    app.run(host='127.0.0.2', port=80, debug=True)
