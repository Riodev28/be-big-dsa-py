from typing import Annotated
from pydantic import BeforeValidator

ObjectIdStr = Annotated[str, BeforeValidator(str)]