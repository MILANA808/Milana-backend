from typing import Any, Dict


class BaseModel:
    def __init__(self, **data: Any):
        for k, v in data.items():
            setattr(self, k, v)
        self.__dict__.update(data)

    def model_dump(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
