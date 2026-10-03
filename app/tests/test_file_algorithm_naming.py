from types import SimpleNamespace

from app.shared.ai.naming import AIAlgorithmNamer, clean_algorithm_name
from app.features.files.schemas import FileDTOCreateRequest, FileDTOUpdateRequest
from app.features.files.service import FileService


def test_clean_name_strips_quotes_and_trailing_period():
    assert clean_algorithm_name('"Binary Search."\n') == "Binary Search"


def test_clean_name_keeps_only_first_line():
    assert clean_algorithm_name("Merge Sort\nIt splits the list...") == "Merge Sort"


def test_clean_name_unknown_is_none():
    assert clean_algorithm_name("Unknown") is None
    assert clean_algorithm_name("  ") is None


def test_clean_name_is_truncated():
    assert len(clean_algorithm_name("x" * 500)) == 100


class _FailingAI:
    def identify_algorithm(self, code):
        raise RuntimeError("groq down")


def test_ai_failure_never_breaks_naming():
    assert AIAlgorithmNamer(_FailingAI()).name("def f(): pass") is None


class _CountingNamer:
    def __init__(self):
        self.calls = 0

    def name(self, code):
        self.calls += 1
        return f"name-{self.calls}"


class _FakeRepository:
    def __init__(self):
        self.file = None

    def create(self, title, algorithm_name, content, owner):
        self.file = SimpleNamespace(
            title=title, algorithm_name=algorithm_name, content=content
        )
        return self.file

    def get_by_id(self, id, owner):
        return self.file

    def update(self, file, title, algorithm_name, content):
        file.title, file.algorithm_name, file.content = title, algorithm_name, content
        return file


def test_name_is_generated_on_create_and_only_regenerated_when_code_changes():
    namer = _CountingNamer()
    service = FileService(_FakeRepository(), namer=namer)

    file = service.create(FileDTOCreateRequest(title="a.py", content="v1"), owner=None)
    assert file.algorithm_name == "name-1"

    file = service.update("id", FileDTOUpdateRequest(title="b.py", content="v1"), owner=None)
    assert (file.algorithm_name, namer.calls) == ("name-1", 1)

    file = service.update("id", FileDTOUpdateRequest(title="b.py", content="v2"), owner=None)
    assert (file.algorithm_name, namer.calls) == ("name-2", 2)


def test_legacy_file_without_name_gets_one_on_update():
    repository = _FakeRepository()
    repository.file = SimpleNamespace(title="a.py", algorithm_name=None, content="v1")
    service = FileService(repository, namer=_CountingNamer())

    file = service.update("id", FileDTOUpdateRequest(title="a.py", content="v1"), owner=None)
    assert file.algorithm_name == "name-1"
