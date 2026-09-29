import anyio
from mongoengine import connect, disconnect, get_connection
from pymongo.errors import PyMongoError

from .config import settings
from .exceptions import FailedDatabaseConnection


class Database:
    async def init_db(self) -> None:
        try:
            connect(
                db=settings.db_name,
                host=settings.mongo_url,
                serverSelectionTimeoutMS=5000,
            )
            await anyio.to_thread.run_sync(self._ping_sync)
        except PyMongoError as e:
            disconnect()
            raise FailedDatabaseConnection(
                f"It was not possible to connect with {settings.mongo_url}"
            ) from e

    async def shutdown_db(self) -> None:
        disconnect()

    async def ping(self) -> bool:
        """Health check: True if Mongo response."""
        try:
            await anyio.to_thread.run_sync(self._ping_sync)
            return True
        except PyMongoError:
            return False

    @staticmethod
    def _ping_sync() -> None:
        get_connection().admin.command("ping")