"""
game_logic.py — Data classes, state machine enum, and scoring helpers.

This file manages the pure game rules and data structures.
No hardware imports are used here to ensure the logic remains independent.
"""

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List

# Import the updated color options instead of the generic DISTANCE_OPTIONS
from config import (
    CONFIG, 
    EMOTION_OPTIONS, 
    GESTURE_OPTIONS, 
    LEFT_COLOR_OPTIONS, 
    RIGHT_COLOR_OPTIONS
)

# ---------------------------------------------------------------------------
# Game state enum
# ---------------------------------------------------------------------------

class GameState(Enum):
    """Enumeration of all possible states in the game's state machine."""
    INTRO             = auto()
    READY_PROMPT      = auto()   # "Are you ready to start?" → waits for button press
    ROUND_START       = auto()
    COUNTDOWN         = auto()
    HOLD              = auto()
    DETECT            = auto()
    RESULT            = auto()
    SHOW_SCORE_PROMPT = auto()   # "Show score? Press button" → waits for button press
    FINAL_SCORE       = auto()
    PLAY_AGAIN_PROMPT = auto()   # "Play again? Press button" → waits for button press


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RoundTarget:
    """The randomly generated target combination that the player must match for one round."""
    emotion        : str   # One of EMOTION_OPTIONS
    left_gesture   : str   # One of GESTURE_OPTIONS
    right_gesture  : str   # One of GESTURE_OPTIONS
    left_distance  : str   # One of LEFT_COLOR_OPTIONS (Pink or Red)
    right_distance : str   # One of RIGHT_COLOR_OPTIONS (Blue or Green)


@dataclass
class DetectionResult:
    """What the camera and sensors actually detected at the snapshot moment."""
    emotion        : Optional[str] = None
    left_gesture   : Optional[str] = None
    right_gesture  : Optional[str] = None
    left_distance  : Optional[str] = None
    right_distance : Optional[str] = None

    def matches(self, target: RoundTarget) -> bool:
        """
        Compare detected results against the target.
        Returns True ONLY if every single field perfectly matches the target.
        """
        return (
            self.emotion        == target.emotion        and
            self.left_gesture   == target.left_gesture   and
            self.right_gesture  == target.right_gesture  and
            self.left_distance  == target.left_distance  and
            self.right_distance == target.right_distance
        )


@dataclass
class RoundRecord:
    """A complete record of one finished round, used later for the final score breakdown."""
    round_num : int
    target    : RoundTarget
    detection : DetectionResult
    passed    : bool


# ---------------------------------------------------------------------------
# Factory / Helper functions
# ---------------------------------------------------------------------------

def random_target() -> RoundTarget:
    """
    Generate a random target by picking independently from each option list.
    Updated to explicitly extract specific color zones for left and right hands.
    """
    return RoundTarget(
        emotion        = random.choice(EMOTION_OPTIONS),
        left_gesture   = random.choice(GESTURE_OPTIONS),
        right_gesture  = random.choice(GESTURE_OPTIONS),
        left_distance  = random.choice(LEFT_COLOR_OPTIONS),   # Extracts Pink or Red
        right_distance = random.choice(RIGHT_COLOR_OPTIONS),  # Extracts Blue or Green
    )


def compute_score(records: List[RoundRecord]) -> int:
    """Calculate and return the total number of rounds that the player passed."""
    return sum(1 for r in records if r.passed)


def game_passed(score: int) -> bool:
    """Return True if the player's total score meets or exceeds the pass threshold."""
    return score >= CONFIG["pass_threshold"]