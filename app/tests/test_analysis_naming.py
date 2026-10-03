from app.features.spatial_complexity.request import SpatialComplexityRequest
from app.features.spatial_complexity.service import SpatialComplexityService
from app.features.temporal_complexity.request import TemporalComplexityRequest
from app.features.temporal_complexity.service import TemporalComplexityService
from app.shared.cache.service import CacheService

CODE = "def f(nums):\n    for n in nums:\n        print(n)\n"


class _DictClient:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex_ttl=None):
        self.store[key] = value


class _ListRecorder:
    def __init__(self):
        self.records = []

    def record(self, record):
        self.records.append(record)


class _CountingNamer:
    def __init__(self, answer="Linear Scan"):
        self.answer = answer
        self.calls = 0

    def name(self, code):
        self.calls += 1
        return self.answer


def _services(namer, recorder):
    cache = CacheService(_DictClient())
    return (
        TemporalComplexityService(cache, ai=None, recorder=recorder, namer=namer),
        SpatialComplexityService(cache, ai=None, recorder=recorder, namer=namer),
    )


async def test_untitled_analysis_is_named_by_ai():
    namer, recorder = _CountingNamer(), _ListRecorder()
    temporal, _ = _services(namer, recorder)

    await temporal.analyze(TemporalComplexityRequest(code=CODE), user_id="u1")

    assert recorder.records[0].title == "Linear Scan"


async def test_temporal_and_spatial_share_one_naming_call():
    namer, recorder = _CountingNamer(), _ListRecorder()
    temporal, spatial = _services(namer, recorder)

    await temporal.analyze(TemporalComplexityRequest(code=CODE), user_id="u1")
    await spatial.analyze(SpatialComplexityRequest(code=CODE), user_id="u1")

    assert namer.calls == 1
    assert [r.title for r in recorder.records] == ["Linear Scan", "Linear Scan"]


async def test_title_from_request_wins_and_skips_ai():
    namer, recorder = _CountingNamer(), _ListRecorder()
    temporal, _ = _services(namer, recorder)

    await temporal.analyze(TemporalComplexityRequest(code=CODE, title="Mine"), user_id="u1")

    assert (recorder.records[0].title, namer.calls) == ("Mine", 0)


async def test_unknown_name_is_retried_next_time():
    namer, recorder = _CountingNamer(answer=None), _ListRecorder()
    temporal, _ = _services(namer, recorder)

    for _ in range(2):
        await temporal.analyze(TemporalComplexityRequest(code=CODE), user_id="u1")

    assert recorder.records[0].title is None
    assert namer.calls == 2


async def test_anonymous_runs_are_not_named():
    namer = _CountingNamer()
    temporal, _ = _services(namer, _ListRecorder())

    await temporal.analyze(TemporalComplexityRequest(code=CODE), user_id=None)

    assert namer.calls == 0
