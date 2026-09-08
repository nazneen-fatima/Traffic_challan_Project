
from ultralytics import YOLO


# ============================================================
# LOAD VIOLATION DETECTION MODEL
# ============================================================

MODEL_PATH = "models/violation_detector.pt"

model = YOLO(MODEL_PATH)


# ============================================================
# DETECT TRAFFIC VIOLATIONS
# ============================================================

def detect_violation(image_path):

    results = model.predict(
        source=image_path,
        conf=0.25
    )

    result = results[0]

    detections = []

    for box in result.boxes:

        class_id = int(box.cls[0])

        class_name = result.names[class_id]

        confidence = float(box.conf[0])

        detections.append({
            "class_name": class_name,
            "confidence": confidence
        })

    return detections

