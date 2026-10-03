from collections import defaultdict
from datetime import datetime
from typing import Any

from bson import ObjectId

from app.shared.analysis import AnalysisKind
from app.shared.ast.complexity import ComplexityClass

from .metrics import Month, NotationCount
from .models import AnalysisRecordModel

# Columns the history list needs; skips the heavy `code` and `report`
_LIST_FIELDS = ("id", "title", "kind", "complexity", "complexity_class", "language", "created_at")


class AnalysisRecordRepository:
    """
    Read queries over analysis history. Aggregations run inside MongoDB so
    only small summaries (counts per class/month) travel to the app, no
    matter how many records a user has.
    """

    def count(
        self,
        user_id: str,
        kind: AnalysisKind,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> int:
        filters = self._scope(user_id, kind)
        if since is not None:
            filters["created_at__gte"] = since
        if until is not None:
            filters["created_at__lt"] = until
        return AnalysisRecordModel.objects(**filters).count()

    def average_duration_ms(self, user_id: str, kind: AnalysisKind) -> float | None:
        rows = self._aggregate(
            self._scope(user_id, kind),
            [{"$group": {"_id": None, "avg": {"$avg": "$duration_ms"}}}],
        )
        return rows[0]["avg"] if rows else None

    def latest_notation_counts(self, user_id: str, kind: AnalysisKind) -> list[NotationCount]:
        """How many *distinct snippets* fall under each notation. A snippet is
        identified by its fingerprint and counted once, by its latest result."""
        rows = self._aggregate(
            self._scope(user_id, kind),
            [
                {"$sort": {"created_at": -1}},
                {
                    "$group": {
                        "_id": "$fingerprint",
                        "notation": {"$first": "$complexity"},
                        "cls": {"$first": "$complexity_class"},
                    }
                },
                {
                    "$group": {
                        "_id": {"notation": "$notation", "cls": "$cls"},
                        "count": {"$sum": 1},
                    }
                },
            ],
        )
        return [
            NotationCount(
                notation=row["_id"]["notation"],
                complexity_class=ComplexityClass(row["_id"]["cls"]),
                count=row["count"],
            )
            for row in rows
        ]

    def monthly_class_counts(
        self, kind: AnalysisKind, since: datetime, user_id: str | None = None
    ) -> dict[Month, list[tuple[ComplexityClass, int]]]:
        """Distinct snippets per (month, class). `user_id=None` = all users."""
        filters: dict[str, Any] = {"kind": kind.value, "created_at__gte": since}
        if user_id is not None:
            filters["user"] = ObjectId(user_id)

        rows = self._aggregate(
            filters,
            [
                {"$sort": {"created_at": -1}},
                {
                    "$group": {
                        "_id": {
                            "user": "$user",
                            "fingerprint": "$fingerprint",
                            "year": {"$year": "$created_at"},
                            "month": {"$month": "$created_at"},
                        },
                        "cls": {"$first": "$complexity_class"},
                    }
                },
                {
                    "$group": {
                        "_id": {"year": "$_id.year", "month": "$_id.month", "cls": "$cls"},
                        "count": {"$sum": 1},
                    }
                },
            ],
        )

        by_month: dict[Month, list[tuple[ComplexityClass, int]]] = defaultdict(list)
        for row in rows:
            key = row["_id"]
            by_month[(key["year"], key["month"])].append(
                (ComplexityClass(key["cls"]), row["count"])
            )
        return by_month

    def list_page(
        self, user_id: str, kind: AnalysisKind | None, limit: int, offset: int
    ) -> tuple[list[AnalysisRecordModel], int]:
        filters: dict[str, Any] = {"user": ObjectId(user_id)}
        if kind is not None:
            filters["kind"] = kind.value

        query = AnalysisRecordModel.objects(**filters)
        items = list(query.order_by("-created_at").only(*_LIST_FIELDS).skip(offset).limit(limit))
        return items, query.count()

    def get(self, id: str, user_id: str) -> AnalysisRecordModel | None:
        if not ObjectId.is_valid(id):
            return None
        return AnalysisRecordModel.objects(id=id, user=ObjectId(user_id)).first()

    @staticmethod
    def _scope(user_id: str, kind: AnalysisKind) -> dict[str, Any]:
        return {"user": ObjectId(user_id), "kind": kind.value}

    @staticmethod
    def _aggregate(filters: dict[str, Any], pipeline: list[dict]) -> list[dict]:
        return list(AnalysisRecordModel.objects(**filters).aggregate(pipeline))
