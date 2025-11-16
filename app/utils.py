# app/utils.py
from flask import request, abort
from pydantic import BaseModel, ValidationError
from typing import TypeVar, Type

T = TypeVar("T", bound=BaseModel)


def validate_json(model: Type[T]) -> T:
    if not request.is_json:
        abort(400, description="JSON payload required")
    try:
        return model.model_validate(request.get_json())
    except ValidationError as e:
        abort(422, description=e.errors())


def validate_form(model: Type[T]) -> T:
    try:
        return model.model_validate(request.form.to_dict())
    except ValidationError as e:
        abort(422, description=e.errors())


def validate_query(model: Type[T]) -> T:
    try:
        return model.model_validate(request.args.to_dict())
    except ValidationError as e:
        abort(422, description=e.errors())