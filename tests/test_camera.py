"""
test_camera.py — Confirm picamzero captures frames and the emotion model runs.

Run:  python test_camera.py
Takes 5 snapshots one second apart and prints the predicted emotion for each.
"""

import time
import json
import numpy as np
import cv2
from picamzero import Camera
from config import CONFIG

try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite  # type: ignore

# Load model config
with open('../' +CONFIG["model_config_path"]) as f: # added ../ bc in /v2/ folder
    cfg = json.load(f)

img_size    = cfg["img_size"]
class_names = cfg["class_names"]
in_scale    = cfg["in_scale"]
in_zero     = cfg["in_zero"]
out_scale   = cfg["out_scale"]
out_zero    = cfg["out_zero"]

# Load model
interp = tflite.Interpreter(model_path='../' +CONFIG["emotion_model_path"]) # added ../ bc in /v2/ folder
interp.allocate_tensors()
in_idx  = interp.get_input_details()[0]["index"]
out_idx = interp.get_output_details()[0]["index"]

cam = Camera()
print("Camera ready. Taking 5 snapshots...\n")

try:
    for i in range(1):
        time.sleep(2.0) 
        frame = cam.capture_array()  # RGB numpy array

        # Preprocess
        img = cv2.resize(frame, (img_size, img_size))
        img_q = np.clip(
            np.round(img.astype(np.float32) / in_scale + in_zero), 0, 255
        ).astype(np.uint8)
        tensor = img_q[np.newaxis, ...]

        # Infer
        interp.set_tensor(in_idx, tensor)
        interp.invoke()
        raw   = interp.get_tensor(out_idx)[0]
        probs = (raw.astype(np.float32) - out_zero) * out_scale
        exp   = np.exp(probs - probs.max())
        probs = exp / exp.sum()

        best_idx  = int(np.argmax(probs))
        label     = class_names[best_idx]
        confidence = float(probs[best_idx])

        print(f"Snapshot {i+1}: {label} ({confidence:.1%})")
        time.sleep(1.0)
finally:
    #cam.close() # no close()
    pass

print("\nDone.")
