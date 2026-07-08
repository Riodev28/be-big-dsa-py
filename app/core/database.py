from mongoengine import connect, disconnect, get_connection
from .config import settings
from .exceptions import FailedDatabaseConnection
import anyio

class Database():
        
    async def init_db(self):
        try:
            connect(db=settings.db_name,host=settings.mongo_url)
        except Exception:
            raise FailedDatabaseConnection
        
    async def shutdown_db(self):
        disconnect()
        
    async def ping(self):
        """ Verify if database is connected or not """
        try:
            await anyio.to_thread.run_sync(lambda: get_connection().admin.command("ping"))
            return True
        except Exception:
            return False