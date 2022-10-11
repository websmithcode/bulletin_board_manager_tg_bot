import sys
from utils.database import AdminDatabase


class Commands:
    @staticmethod
    def add_admin(args):
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


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Not enough arguments')
        raise SystemExit
    # Arg --add-admin <user_id> <username> <fullname> <sign>
    if sys.argv[1] == '--add-admin':
        Commands.add_admin(sys.argv)
