from tinydb import TinyDB, Query

admin = Query()
class AdminDatabase(object):
    def __init__(self, *args, **kwargs):
        self.__db = TinyDB(kwargs.pop('db', 'admins'))


    @property
    def admins(self):
        return self.__db.all()


    @admins.setter
    def admins(self, value):
        self.__db.insert({'id': value.pop('id'), 
                          'username': value.pop('username'), 
                          'fullname': value.pop('fullname')})


    def remove_admin(self, **kwargs):
        if kwargs.get('username'):
            self.__db.remove(admin.username == kwargs.get('username'))
        elif kwargs.get('fullname'):
            self.__db.remove(admin.fullname == kwargs.get('fullname'))
        elif kwargs.get('id'):
            self.__db.remove(admin.id == kwargs.get('id'))
            

tag = Query()
class TagDatabase():
    def __init__(self, *args, **kwargs):
        self.__db = TinyDB(kwargs.pop('db', 'tags'))
        
    
    @property
    def tags(self):
        return self.__db.all()
    
    @tags.setter
    def tags(self, value: str):
        self.__db.insert({'tag': value})
        
    
    def remove_tag(self, value: str):
        self.__db.remove(tag.tag == value)