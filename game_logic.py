"""
game_logic.py — Data classes, state machine enum, and scoring helpers.

No hardware imports here — pure Python logic only.
"""

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List

from config import CONFIG, EMOTION_OPTIONS, GESTURE_OPTIONS, DISTANCE_OPTIONS


# ---------------------------------------------------------------------------
# Game state enum
# ---------------------------------------------------------------------------

class GameState(Enum):
    INTRO             = auto()
    READY_PROMPT      = auto()   # "Are you ready to start?" → button
    ROUND_START       = auto()
    COUNTDOWN         = auto()
    HOLD              = auto()
    DETECT            = auto()
    RESULT            = auto()
    SHOW_SCORE_PROMPT = auto()   # "Show score? Press button" → button
    FINAL_SCORE       = auto()
    PLAY_AGAIN_PROMPT = auto()   # "Play again? Press button" → button


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RoundTarget:
    """The randomly generated target combination for one round."""
    emotion        : str   # one of EMOTION_OPTIONS
    left_gesture   : str   # one of GESTURE_OPTIONS
    right_gesture  : str   # one of GESTURE_OPTIONS
    left_distance  : str   # one of DISTANCE_OPTIONS
    right_distance : str   # one of DISTANCE_OPTIONS


@dataclass
class DetectionResult:
    """What was actually detected at snapshot time."""
    emotion        : Optional[str] = None
    left_gesture   : Optional[str] = None
    right_gesture  : Optional[str] = None
    left_distance  : Optional[str] = None
    right_distance : Optional[str] = None

    def matches(self, target: RoundTarget) -> bool:
        """Return True only if every field matches the target."""
        return (
            self.emotion        == target.emotion        and
            self.left_gesture   == target.left_gesture   and
            self.right_gesture  == target.right_gesture  and
            self.left_distance  == target.left_distance  and
            self.right_distance == target.right_distance
        )


@dataclass
class RoundRecord:
    """Full record of one completed round (used for final score screen)."""
    round_num : int
    target    : RoundTarget
    detection : DetectionResult
    passed    : bool


# ---------------------------------------------------------------------------
# Factory / helpers
# ---------------------------------------------------------------------------

def random_target() -> RoundTarget:
    """Generate a random target by picking independently from each option list."""
    return RoundTarget(
        emotion        = random.choice(EMOTION_OPTIONS),
        left_gesture   = random.choice(GESTURE_OPTIONS),
        right_gesture  = random.choice(GESTURE_OPTIONS),
        left_distance  = random.choice(DISTANCE_OPTIONS),
        right_distance = random.choice(DISTANCE_OPTIONS),
    )


def compute_score(records: List[RoundRecord]) -> int:
    """Return the number of rounds that were passed."""
    return sum(1 for r in records if r.passed)


def game_passed(score: int) -> bool:
    """Return True if the player passed the game overall."""
    return score >= CONFIG["pass_threshold"]
