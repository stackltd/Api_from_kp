token = 'ВАШ ТОКЕН'


# RANDOM_MOVIE = '/v1/movie/random'
RANDOM_MOVIE = '/v1.4/movie/random'

# примеры query параметров
# query = {"notNullFields": "description"}
# query = {"notNullFields": "description", "genres.name": "фантастика", "rating.kp": '3-10'}
# query = {"notNullFields": "description", "genres.name": "ужасы", "rating.kp": '3-10'}
# query = {"notNullFields": "description", "genres.name": ("фантастика", "триллер", "боевик", "комедия"), "rating.kp": '3-10'}
query = {"notNullFields": "description", "genres.name": ("фантастика", "триллер", "боевик", "комедия"), "rating.kp": '3-10', "countries.name": ("США", "Великобритания")}
# query= {"notNullFields": "description", "countries.name": "СССР"}
# query = {"notNullFields": "description", "rating.kp": '3-10', "genres.name": '!мультфильм'}
# query= {"notNullFields": "description", "countries.name": ("США", "Великобритания")}
