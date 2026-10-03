from bson import ObjectId

from app.shared.analysis import AnalysisRecord

from .models import AnalysisRecordModel


class MongoAnalysisRecorder:
    """Adapter for the `AnalysisRecorder` port declared in app.shared.analysis."""

    def record(self, record: AnalysisRecord) -> None:
        AnalysisRecordModel(
            user=ObjectId(record.user_id),
            kind=record.kind.value,
            title=record.title,
            language=record.language,
            code=record.code,
            complexity=record.complexity,
            complexity_class=record.complexity_class.value,
            fingerprint=record.fingerprint,
            duration_ms=record.duration_ms,
            cached=record.cached,
            ai_explained=record.ai_explained,
            report=record.report,
        ).save()
