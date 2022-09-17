"""Модуль предназначенный для работы с базой данных
"""
from typing import Dict, List
from tinydb import TinyDB, Query
from utils.logger import log

admin = Query()
class AdminDatabase():
    """Класс представляюший объект базы администраторов.
    """
    def __init__(self, **kwargs):
        self.__db = TinyDB(kwargs.pop('db', 'admins'), encoding='utf8')


    @property
    def admins(self) -> List[Dict]:
        """Поле представляющее список администраторов.

        Returns:
            List[Dict]: Список документов администраторов.
        """
        log.debug('Вызван список администраторов!')
        return self.__db.all()


    @admins.setter
    def admins(self, value: Dict):
        """Сеттер поля администраторов, позволяющий добавлять документы в базу.
        """
        _ = self.__db.insert({'id': value.pop('id'),
                          'username': value.pop('username'),
                          'fullname': value.pop('fullname')})
        log.info('Запись администратора успешно добавлена! Id: %s.', str(_))


    def remove_admin(self, **kwargs):
        """Метод позволяющий удалять администраторов из базы.
        """
        if kwargs.get('username'):
            _ = self.__db.remove(admin.username == kwargs.get('username'))
        elif kwargs.get('fullname'):
            _ = self.__db.remove(admin.fullname == kwargs.get('fullname'))
        elif kwargs.get('id'):
            _ = self.__db.remove(admin.id == kwargs.get('id'))
        log.info('Администратор удален! Id: %s.', str(_))


tag = Query()
class TagDatabase():
    """Класс представляюший объект базы тегов.
    """
    def __init__(self, **kwargs):
        self.__db = TinyDB(kwargs.pop('db', 'tags'), encoding='utf8')


    @property
    def tags(self):
        """Поле представляющее список тегов.

        Returns:
            List[Dict]: Список документов тегов.
        """
        log.debug('Вызван список тегов!')
        return self.__db.all()


    @tags.setter
    def tags(self, value: str):
        """Сеттер поля тегов, позволяющий добавлять документы в базу.
        """
        _ = self.__db.insert({'tag': value})
        log.info('Тег успешно добавлен! Id: %s.', str(_))


    def remove_tag(self, value: str):
        """Метод позволяющий удалять теги из базы.
        """
        _ = self.__db.remove(tag.tag == value)
        log.info('Тег удален! Id: %s.', str(_))
