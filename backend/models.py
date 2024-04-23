# Handle Database models
from pydantic import BaseModel

class Workout(BaseModel):
    id: int
    uid: int
    date: str
    eid: int
    sid: int

class Sets(BaseModel):
    reps: int
    weights: float

class Exercises(BaseModel):
    name: str
    muscle_group: str
    icon: str