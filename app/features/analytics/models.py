from mongoengine import (
    CASCADE,
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    FloatField,
    ReferenceField,
    StringField,
)

from app.features.auth.models import UserModel
from app.shared.analysis import AnalysisKind
from app.shared.ast.complexity import ComplexityClass
from app.shared.helpers.datetime_helper import utcnow


class AnalysisRecordModel(Document):
    """One finished analysis. Append-only: history is never edited."""

    user = ReferenceField(UserModel, required=True, reverse_delete_rule=CASCADE)
    kind = StringField(required=True, choices=[k.value for k in AnalysisKind])

    title = StringField(max_length=100)
    language = StringField(required=True)
    code = StringField(required=True)

    complexity = StringField(required=True)
    # The class is stored, not the health score, so the scoring policy can
    # change in code without migrating data
    complexity_class = StringField(
        required=True, choices=[c.value for c in ComplexityClass]
    )
    fingerprint = StringField(required=True)

    duration_ms = FloatField(required=True)
    cached = BooleanField(default=False)
    ai_explained = BooleanField(default=False)
    report = DictField()

    created_at = DateTimeField(default=utcnow)

    meta = {
        "collection": "analyses",
        "indexes": [
            # every per-user dashboard query filters on (user, kind) and
            # sorts or ranges on created_at
            ("user", "kind", "-created_at"),
            # platform-wide baseline for the trends chart
            ("kind", "created_at"),
        ],
    }
