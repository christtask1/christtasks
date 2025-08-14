import json
from functools import lru_cache


@lru_cache(maxsize=1)
def load_profile(path: str = "app/profiles/apologetics_debate.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


