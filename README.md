# bulletin_board_manager_tg_bot

> All commands must be runned from virtual environment (enable it with `poetry shell`) <br>
>Or run with `poetry run <command...>`

This is telegram bot - bulletin board group manager.<br>
He recieves messages from group, then copy it to moderators.<br>
Message in the group is deleted and placed back from bot, after success moderation with added hashtags, author contact and admin sign.


## Init
- In this project - used [poetry](https://python-poetry.org) dependency manager. Run `poetry install` for install requrements.
- Copy `example.config.ini` to `config.ini` and fill it with your data

## Run
- Just run `python main.py`

## Commands
### Add new admin to database
```python commands.py --add-admin <user_id*> <username*> <fullname*> <sign>```
