from utils.logger import log

async def callback_query(call):
    log.info('callback data from callback query id %s is \'%s\'', call.id, call.data)