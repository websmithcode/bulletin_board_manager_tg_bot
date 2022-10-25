""" Commands cli script """
import sys
from utils.database import AdminDatabase


class Commands:
    """ Commands class """
    @staticmethod
    def add_admin(args):
        """ Add new admin to database
            :param args: list of arguments
            :param args[2]: user_id
            :param args[3]: username
            :param args[4]: fullname
            :param args[5]: sign"""
        if len(args) < 5:
            print('Not enough arguments')
            raise SystemExit

        params = {
            'user_id': args[2],
            'username': args[3],
            'fullname': args[4],
            'sign': args[5] if len(args) > 5 else None
        }
        db_admins = AdminDatabase()
        db_admins.add_admin(**params)

    @staticmethod
    def remove_admin(username):
        """ Remove admin from database
            :param username: username of admin """
        db_admins = AdminDatabase()
        db_admins.remove_admin(username=username)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Not enough arguments')
        raise SystemExit
    # Arg --add-admin <user_id> <username> <fullname> <sign>
    if sys.argv[1] == '--add-admin':
        Commands.add_admin(sys.argv)
    # Arg --remove-admin <username>
    elif sys.argv[1] == '--remove-admin':
        Commands.remove_admin(sys.argv[2])
