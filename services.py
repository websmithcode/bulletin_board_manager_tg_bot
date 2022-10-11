from utils.database import AdminDatabase


class Services:
    @staticmethod
    def add_admin(bot, fullname, username, user_id, sign):
        db_admins = AdminDatabase()
        db_admins.add_admin(username, fullname, user_id, sign)
