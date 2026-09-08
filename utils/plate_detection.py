


from ultralytics import YOLO
import cv2
import os


# ============================================================
# LOAD NUMBER PLATE MODEL
# ============================================================

MODEL_PATH = "models/number_plate_detector.pt"

model = YOLO(MODEL_PATH)


# ============================================================
# NUMBER PLATE DETECTION
# ============================================================

def detect_plate(image_path):

    # --------------------------------------------------------
    # CREATE OUTPUTS FOLDER
    # --------------------------------------------------------

    os.makedirs("outputs", exist_ok=True)


    # --------------------------------------------------------
    # RUN YOLO NUMBER PLATE DETECTION
    # --------------------------------------------------------

    results = model.predict(
        source=image_path,
        conf=0.25
    )

    result = results[0]

    image = cv2.imread(image_path)

    plates = []

    cropped_plate_path = None


    # ========================================================
    # PROCESS DETECTED PLATES
    # ========================================================

    for box in result.boxes:

        x1, y1, x2, y2 = box.xyxy[0].tolist()

        confidence = float(box.conf[0])

        x1 = int(x1)
        y1 = int(y1)
        x2 = int(x2)
        y2 = int(y2)


        plates.append({
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
            "confidence": confidence
        })


        # ----------------------------------------------------
        # DRAW BOUNDING BOX
        # ----------------------------------------------------

        cv2.rectangle(
            image,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            3
        )


        cv2.putText(
            image,
            "Number Plate",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )


        # ----------------------------------------------------
        # CROP NUMBER PLATE
        # ----------------------------------------------------

        cropped_plate = image[
            y1:y2,
            x1:x2
        ]


        cropped_plate_path = (
            "outputs/cropped_plate.jpg"
        )


        cv2.imwrite(
            cropped_plate_path,
            cropped_plate
        )


        # ----------------------------------------------------
        # USE FIRST DETECTED PLATE
        # ----------------------------------------------------

        break


    # ========================================================
    # SAVE IMAGE WITH BOUNDING BOX
    # ========================================================

    detected_image_path = (
        "outputs/detected_plate.jpg"
    )


    cv2.imwrite(
        detected_image_path,
        image
    )


    return (
        plates,
        detected_image_path,
        cropped_plate_path
    )

