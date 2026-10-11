import json
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class ResponseValidator:
    @staticmethod
    def validate_json(raw_json: str, schema_class: Type[T]) -> T:
        clean_json = raw_json.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean_json)
        return schema_class(**parsed)
