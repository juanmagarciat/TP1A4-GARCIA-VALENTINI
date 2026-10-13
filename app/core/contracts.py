from pydantic import ConfigDict, model_validator
from sqlmodel import SQLModel


class Contract(SQLModel):
    model_config = ConfigDict(extra="forbid")


class PartialUpdate(Contract):
    @model_validator(mode="before")
    @classmethod
    def reject_null_required_fields(cls, values):
        if isinstance(values, dict):
            for name, value in values.items():
                if value is None and name != "genero_id":
                    raise ValueError(
                        f"El campo {name} no admite null; omitirlo conserva su valor."
                    )
        return values
