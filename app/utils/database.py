"""Модуль предназначенный для работы с базой данных"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from tinydb import Query, TinyDB, where
from tinydb.storages import MemoryStorage

from utils.logger import log
from utils.helpers import Singletone

admin = Query()
memory = TinyDB(storage=MemoryStorage)

# Create db directory and database files if not exists
Path("db").mkdir(parents=True, exist_ok=True)


class AdminDatabase(metaclass=Singletone):
    """Класс представляюший объект базы администраторов."""

    def __init__(self, **kwargs):
        self.__db = TinyDB(kwargs.pop('db', 'db/admins.json'), encoding='utf8')

    @property
    def admins(self) -> List[Dict]:
        """Поле представляющее список администраторов.

        Returns:
            List[Dict]: Список документов администраторов.
        """
        log.info('Вызван список администраторов!')
        return self.__db.all()

    @admins.setter
    def admins(self, value: Dict):
        """Сеттер поля администраторов, позволяющий добавлять документы в базу."""
        self.add_admin(**value)

    def add_admin(self, username: str, fullname: str, user_id: int, sign: str):
        """Метод позволяющий добавлять администраторов в базу."""
        _ = self.__db.insert({
            'id': int(user_id),
            'username': username,
            'fullname': fullname,
            'sign': sign
        })
        log.info('Запись администратора успешно добавлена! Id: %s.', str(_))

    def update(self, admin_id: int, query: Dict):
        """Метод позволяющий обновить записи в базе.

        Args:
            `admin_id (int)`: ID администратора.
            `query (Dict)`: Запись изменений.
        """
        self.__db.update(query, admin.id == admin_id)

    def remove_admin(self, **kwargs):
        """Метод позволяющий удалять администраторов из базы."""
        if kwargs.get('username'):
            _ = self.__db.remove(admin.username == kwargs.get('username'))
        elif kwargs.get('fullname'):
            _ = self.__db.remove(admin.fullname == kwargs.get('fullname'))
        elif kwargs.get('id'):
            _ = self.__db.remove(admin.id == int(kwargs.get('id')))
        log.info('Администратор удален! Id: %s.', str(_))

    def get_admin_by_id(self, admin_id: int) -> Dict:
        """Метод позволяющий получить администратора по его ID.

        Args:
            `id (int)`: ID администратора.

        Returns:
            Dict: Документ администратора.
        """
        return self.__db.get(admin.id == admin_id)


tag = Query()


class TagDatabase(metaclass=Singletone):
    """Класс представляюший объект базы тегов."""

    def __init__(self, **kwargs):
        self.__db = TinyDB(kwargs.pop('db', 'db/tags.json'), encoding='utf8')

    @property
    def tags(self) -> List[Dict]:
        """Поле представляющее список тегов.

        Returns:
            `List[Dict]`: Список документов тегов.
        """
        log.info('Вызван список тегов!')
        return self.__db.all()

    @tags.setter
    def tags(self, value: str):
        """Сеттер поля тегов, позволяющий добавлять документы в базу."""
        _ = self.__db.insert({'tag': value})
        log.info('Тег успешно добавлен! Id: %s.', str(_))

    def remove_tag(self, value: str):
        """Метод позволяющий удалять теги из базы."""
        _ = self.__db.remove(tag.tag == value)
        log.info('Тег удален! Id: %s.', str(_))


class MessagesToPreventDeletingDB(metaclass=Singletone):
    """Class, that represents database of messages to prevent deleting."""

    def __init__(self, **kwargs):
        db_path = kwargs.pop('db', 'db/messages_to_prevent_deleting.json')
        self.db = TinyDB(db_path, encoding='utf8')

    def add(self, message_id: int):
        """Method that adds message to database."""
        self.db.insert({'message_id': message_id})

    def remove(self, message_id: int):
        """Method that removes message from database."""
        self.db.remove(where('message_id') == message_id)

    def has(self, message_id: int) -> bool:
        """Method that checks if message is in database."""
        return self.db.contains(where('message_id') == message_id)


class BannedSenders(metaclass=Singletone):
    """Class, that represents database of banned senders."""

    def __init__(self, **kwargs):
        db_path = kwargs.pop('db', 'db/banned_senders.json')
        self.db = TinyDB(db_path, encoding='utf8')

    @staticmethod
    def now(add_days: int = 0, subtract_days: int = 0) -> str:
        """Property, that returns timestamp"""
        now = datetime.now()
        if add_days:
            now += timedelta(days=add_days)
        elif subtract_days:
            now -= timedelta(days=subtract_days)
        return now.timestamp()

    def add(self, sender_id: int):
        """Method that adds user to database."""
        self.remove(sender_id)
        self.db.insert({'sender_id': sender_id, 'date': self.now()})

    def remove(self, sender_id: int):
        """Method that removes user from database."""
        self.db.remove(where('sender_id') == sender_id)

    def has(self, sender_id: int, days_period=7) -> bool:
        """Method that checks if user is in database."""
        selector = (where('sender_id') == sender_id) \
            & (where('date') > self.now(subtract_days=days_period))
        return self.db.contains(selector)
