from enum import Enum

class Phase(str, Enum):
    QUESTION = "QUESTION"
    SHOW_ANSWER = "SHOW_ANSWER"
    LEADERBOARD = "LEADERBOARD"
    COUNTDOWN = "COUNTDOWN"
    ENDED = "ENDED"
