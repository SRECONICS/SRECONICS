"""
Real-time ASL gesture classifier using MediaPipe Hands + TFLite (Pi 5 Edition).
Run with: python gesture_classifier.py
"""

import cv2
import numpy as np
import mediapipe as mp
import tflite_runtime.interpreter as tflite
from tts_output import speak

MODEL_PATH  = "models/asl_int8.tflite"
LABELS_PATH = "models/labels.txt"
CONF_THRESH = 0.80
WORD_GAP_MS = 1200          # ms of silence → flush word to TTS

mp_hands   = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

labels = [l.strip() for l in open(LABELS_PATH)]

interp = tflite.Interpreter(MODEL_PATH, num_threads=4)
interp.allocate_tensors()
in_det  = interp.get_input_details()
out_det = interp.get_output_details()


def classify_landmarks(landmarks_flat):
    inp = landmarks_flat.reshape(in_det[0]["shape"]).astype("float32")
    interp.set_tensor(in_det[0]["index"], inp)
    interp.invoke()
    probs = interp.get_tensor(out_det[0]["index"])[0]
    idx   = int(probs.argmax())
    return labels[idx], float(probs[idx])


def run():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    word_buf, last_char, last_time = [], "", 0

    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.5,
    ) as hands:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = hands.process(rgb)

            if res.multi_hand_landmarks:
                lm   = res.multi_hand_landmarks[0]
                flat = np.array([[p.x, p.y, p.z] for p in lm.landmark]).flatten()
                char, conf = classify_landmarks(flat)

                if conf >= CONF_THRESH and char != last_char:
                    word_buf.append(char)
                    last_char = char
                    import time; last_time = time.time()

                mp_drawing.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)
                cv2.putText(frame, f"{char}  {conf:.0%}", (30, 50),
                            cv2.FONT_HERSHEY_DUPLEX, 1.4, (0, 220, 0), 2)
            else:
                import time
                if word_buf and (time.time() - last_time) * 1000 > WORD_GAP_MS:
                    word = "".join(word_buf)
                    speak(word)
                    print("Spoke:", word)
                    word_buf.clear()
                    last_char = ""

            cv2.imshow("ASL Translator — Pi 5", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
