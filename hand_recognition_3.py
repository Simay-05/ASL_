import cv2
import os
import mediapipe as mp
import time
import math

class HandTrackingDynamic:
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        self.__mode__ = mode
        self.__maxHands__ = maxHands
        self.__detectionCon__ = detectionCon
        self.__trackCon__ = trackCon
        self.handsMp = mp.solutions.hands
        self.hands = self.handsMp.Hands(
            static_image_mode=mode,
            max_num_hands=maxHands,
            min_detection_confidence=detectionCon,
            min_tracking_confidence=trackCon,
        )
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]

    # -------------------------------------------------
    # 1.  Detect hands but do NOT draw landmarks
    # -------------------------------------------------
    def findFingers(self, frame, draw=False):
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        return frame

    # -------------------------------------------------
    # 2.  Return landmarks & enlarged bounding-box
    #     (draw green rectangle when draw=True)
    # -------------------------------------------------
    def findPosition(self, frame, handNo=0, draw=True):
        xList, yList, bbox = [], [], []
        self.lmsList = []

        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                h, w, _ = frame.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                xList.append(cx)
                yList.append(cy)
                self.lmsList.append([id, cx, cy])

            # larger margin
            margin = 60
            xmin, xmax = min(xList), max(xList)
            ymin, ymax = min(yList), max(yList)
            x1 = max(0, xmin - margin)
            y1 = max(0, ymin - margin)
            x2 = min(w, xmax + margin)
            y2 = min(h, ymax + margin)
            bbox = (x1, y1, x2, y2)

            # store crop coordinates for later save
            self._crop_region = (y1, y2, x1, x2)

            if draw:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        return self.lmsList, bbox

    # (other helper methods unchanged)
    def findFingerUp(self):
        fingers = []
        if len(self.lmsList) < 21:
            return fingers
        # thumb
        if self.lmsList[self.tipIds[0]][1] > self.lmsList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)
        # other fingers
        for id in range(1, 5):
            if self.lmsList[self.tipIds[id]][2] < self.lmsList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers

    def findDistance(self, p1, p2, frame, draw=True, r=15, t=3):
        if len(self.lmsList) < max(p1, p2):
            return 0, frame, []
        x1, y1 = self.lmsList[p1][1:]
        x2, y2 = self.lmsList[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        length = math.hypot(x2 - x1, y2 - y1)
        if draw:
            cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(frame, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(frame, (x2, y2), r, (255, 0, 0), cv2.FILLED)
            cv2.circle(frame, (cx, cy), r, (0, 0, 255), cv2.FILLED)
        return length, frame, [x1, y1, x2, y2, cx, cy]


# -------------------------------------------------
#  MAIN
# -------------------------------------------------
def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    detector = HandTrackingDynamic()
    ptime = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # landmarks off, rectangle on
        frame = detector.findFingers(frame, draw=False)
        lmsList, bbox = detector.findPosition(frame, draw=True)

        # save crop on 'a'
        key = cv2.waitKey(1) & 0xFF
        if key == ord('a') and hasattr(detector, '_crop_region'):
            y1, y2, x1, x2 = detector._crop_region
            hand_crop = frame[y1:y2, x1:x2]
            cv2.imwrite("detect.jpg", hand_crop)
            print("Saved detect.jpg")

        # FPS display
        ctime = time.time()
        fps = 1 / (ctime - ptime)
        ptime = ctime
        cv2.putText(frame, str(int(fps)), (10, 70),
                    cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

        cv2.imshow('frame', frame)
        if key == 27:  # ESC to quit
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
