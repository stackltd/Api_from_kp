import functools
import time
import datetime

def timer(func):
    """
    Декоратор измеряет время работы входящей функции.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        diff = time.time() - start
        diff = str(datetime.timedelta(seconds=diff)).split(':')
        print(f'Программа завершена. Время выполнения: {diff[0]} ч, {diff[1]} мин, {diff[2]:.2} сек')
    return wrapper