"""
detector.py — EmotionDetector (fully implemented) + GestureDetector (stub).

Camera note: picamzero's capture_array() returns an RGB numpy array.
  EmotionDetector.predict() accepts RGB frames directly.
  GestureDetector.detect() also expects RGB frames.

EmotionDetector
    Loads an INT8-quantized EfficientNetB0 TFLite model and model_config.json.
    predict(frame_rgb) → (label, confidence) or (None, 0.0)

GestureDetector  ← TO BE IMPLEMENTED BY TEAM MEMBER
    Stub that always returns {"Left": (None, 0.0), "Right": (None, 0.0)}.
    Replace the body of detect() (and helpers) with the real MediaPipe logic.
    MediaPipe also expects RGB input, so no conversion needed.
"""

import json
import warnings
import numpy as np
import cv2

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        import tensorflow as tf  # type: ignore
        tflite = tf.lite
    except ImportError:
        tflite = None
        warnings.warn("[detector] Neither tflite_runtime nor tensorflow found — "
                      "EmotionDetector will not work.")

from config import CONFIG, EMOTION_OPTIONS


# ---------------------------------------------------------------------------
# EmotionDetector
# ---------------------------------------------------------------------------

class EmotionDetector:
    """
    Wraps an INT8-quantized TFLite emotion model.

    Parameters
    ----------
    model_path            : path to .tflite file
    model_config_path     : path to model_config.json
    confidence_threshold  : minimum softmax probability to accept a prediction
    """

    def __init__(
        self,
        model_path=CONFIG["emotion_model_path"],
        model_config_path=CONFIG["model_config_path"],
        confidence_threshold=CONFIG["emotion_confidence"],
    ):
        self._threshold = confidence_threshold

        # Load model config
        with open(model_config_path, "r") as f:
            cfg = json.load(f)

        self._img_size    = cfg["img_size"]      # int, e.g. 224
        self._class_names = cfg["class_names"]   # list[str], length == num_classes
        self._in_scale    = cfg["in_scale"]      # float
        self._in_zero     = cfg["in_zero"]       # int
        self._out_scale   = cfg["out_scale"]     # float
        self._out_zero    = cfg["out_zero"]      # int

        # Load TFLite interpreter
        self._interp = tflite.Interpreter(model_path=model_path)
        self._interp.allocate_tensors()

        in_detail  = self._interp.get_input_details()[0]
        out_detail = self._interp.get_output_details()[0]
        self._in_idx  = in_detail["index"]
        self._out_idx = out_detail["index"]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _preprocess(self, frame_rgb):
        """
        Convert an RGB numpy frame to a quantized uint8 tensor.

        Steps:
          1. Resize to (img_size, img_size)
          2. Normalise: img = (img / 127.5) - 1.0
          3. Quantize to uint8: q = round(img / in_scale + in_zero)
          4. Add batch dimension → shape (1, img_size, img_size, 3)
        """
        img = cv2.resize(frame_rgb, (self._img_size, self._img_size))
        img = img.astype(np.float32)
        img = (img / 127.5) - 1.0
        img_q = np.round(img / self._in_scale + self._in_zero).astype(np.uint8)
        return img_q[np.newaxis, ...]  # (1, H, W, 3)

    def _dequantize_output(self, raw):
        """Convert INT8 output tensor to float32 logits, then softmax."""
        floats = (raw.astype(np.float32) - self._out_zero) * self._out_scale
        exp = np.exp(floats - floats.max())
        return exp / exp.sum()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, frame_rgb):
        """
        Run inference on a single RGB frame (as returned by picamzero).

        Returns
        -------
        (label, confidence) if a valid emotion is detected above threshold,
        (None, 0.0) otherwise.
        """
        if frame_rgb is None:
            return None, 0.0

        tensor = self._preprocess(frame_rgb)
        self._interp.set_tensor(self._in_idx, tensor)
        self._interp.invoke()

        raw   = self._interp.get_tensor(self._out_idx)  # shape (1, num_classes)
        probs = self._dequantize_output(raw[0])

        best_idx  = int(np.argmax(probs))
        best_prob = float(probs[best_idx])
        label     = self._class_names[best_idx]

        if best_prob < self._threshold or label not in EMOTION_OPTIONS:
            return None, 0.0

        return label, best_prob


# ---------------------------------------------------------------------------
# GestureDetector  — STUB (to be implemented by team member)
# ---------------------------------------------------------------------------

class GestureDetector:
    """
    Detects hand gestures using MediaPipe Hands.

    Input frames should be RGB numpy arrays (picamzero format — no conversion needed
    before passing to MediaPipe, which also expects RGB).

    Expected return format of detect():
        {
            "Left" : (gesture_str, confidence),   # gesture_str in GESTURE_OPTIONS or None
            "Right": (gesture_str, confidence),
        }

    This stub always returns (None, 0.0) for both hands.
    Replace the internals of detect() (and add helpers) to implement the real logic.

    Gesture rules (from CLAUDE.md):
        thumbs_up   : thumb extended, all other fingers curled
        thumbs_down : thumb extended downward (tip.y > ip.y), all others curled
        peace       : index + middle extended, thumb + ring + pinky curled

    Landmark indices:
        Thumb  : tip=4,  ip=3   (x-distance check for extension)
        Index  : tip=8,  pip=6
        Middle : tip=12, pip=10
        Ring   : tip=16, pip=14
        Pinky  : tip=20, pip=18

    Finger extended if tip.y < pip.y (image coordinates).
    Thumb extended if |tip.x - ip.x| > threshold.
    """

    def __init__(self, confidence_threshold=CONFIG["gesture_confidence"]):
        self._threshold = confidence_threshold
        # TODO: initialise MediaPipe Hands here, e.g.:
        #   import mediapipe as mp
        #   self._mp_hands = mp.solutions.hands.Hands(
        #       static_image_mode=True,
        #       max_num_hands=2,
        #       min_detection_confidence=confidence_threshold,
        #   )
        warnings.warn(
            "[detector] GestureDetector is a stub — gesture detection not yet implemented."
        )

    def detect(self, frame_rgb):
        """
        Run hand gesture detection on an RGB frame.

        Returns
        -------
        dict with keys "Left" and "Right", each (gesture_str, confidence).
        gesture_str is a string from GESTURE_OPTIONS, or None if not detected.
        """
        # TODO: replace stub body with real MediaPipe inference, e.g.:
        #
        #   results = self._mp_hands.process(frame_rgb)
        #   output = {"Left": (None, 0.0), "Right": (None, 0.0)}
        #   if results.multi_hand_landmarks:
        #       for landmarks, handedness in zip(
        #           results.multi_hand_landmarks, results.multi_handedness
        #       ):
        #           side    = handedness.classification[0].label  # "Left" or "Right"
        #           gesture = self._classify_landmarks(landmarks, side)
        #           output[side] = gesture
        #   return output

        return {"Left": (None, 0.0), "Right": (None, 0.0)}

    # ------------------------------------------------------------------
    # Landmark classification helpers (to be implemented by team member)
    # ------------------------------------------------------------------

    def _is_finger_extended(self, landmarks, tip_idx, pip_idx):
        """Return True if tip.y < pip.y (tip is above pip in image coords)."""
        # TODO: implement
        raise NotImplementedError

    def _is_thumb_extended(self, landmarks, handedness, threshold=0.04):
        """Return True if |tip.x - ip.x| > threshold."""
        # TODO: implement
        raise NotImplementedError

    def _classify_landmarks(self, landmarks, handedness):
        """
        Apply gesture rules to a single hand's landmarks.

        Returns (gesture_str, confidence) or (None, 0.0).
        """
        # TODO: implement
        raise NotImplementedError
