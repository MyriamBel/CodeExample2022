from django.db import connection
import os.path


def get_file_upload(instance, file=None):
    """
    Строим путь к файлам. Формат: media/app_name/class_name/files/id/file.
    Функция возвзращает путь к файлу для двух случаев - когда пользователь загружает файл извне и когда
    путь должен быть сгенерирован самой системой (в частности, когда генерируем pdf-отчёты и нужно их
    куда-то положить). Эта функция вызывается при сохранении объекта.
    """
    module_name = instance.__module__.split('.')[0]
    class_name = instance.__class__.__name__.lower()
    # Если объект уже был сохранен, то есть имеет id:
    if instance.id:
        some_id = instance.id
    # Если нет - возьмем из бд последовательность и найдем следующий id, который будет присвоен объекту.
    else:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM public.\"{module_name}_{class_name}_id_seq\";")
            some_id = cursor.fetchone()
        some_id = some_id[0]
        if some_id != 0 or some_id is not None:
            some_id += 1
        else:
            some_id = 0
    # если хотим получить весь путь к файлу - пользователь загружает извне.
    if file is not None:
        return f'{module_name}/{class_name}/files/{some_id}/{file}'
    # если нет - строим путь к файлу, который создаем самостоятельно - создадим путь в
    # файловой системе и вернем его.
    else:
        path = os.path.join(module_name, class_name, 'files', str(some_id))
        return path