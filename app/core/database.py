from mongoengine import connect, disconnect, get_connection
from .config import settings
from .exceptions import FailedDatabaseConnection

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
            get_connection().admin.command("ping")
            return True
        except Exception:
            return False