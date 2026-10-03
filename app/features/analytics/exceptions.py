from fastapi import HTTPException, status


class AnalyticsExceptions:
    """Factories for analytics errors. Usage: `raise AnalyticsExceptions.not_found()`."""

    @staticmethod
    def not_found() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )
