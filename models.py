from pydantic import BaseModel


class Game(BaseModel):
    model: str
    word: str
    guesses: int = 1
    solved: bool = False
    error: bool = False
    messages: list[dict] = []
    cost: float = 0.0
