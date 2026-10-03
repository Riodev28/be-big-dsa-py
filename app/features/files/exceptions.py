from fastapi import HTTPException, status


class FileExceptions:
    """Factories for file errors. Usage: `raise FileExceptions.not_found()`."""

    @staticmethod
    def not_found() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )
