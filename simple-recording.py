#recording not in "real time"

import cv2
 
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap.set(cv2.CAP_PROP_FPS, 24.0)

width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)   # float `width`
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)  # float `height`
fps = cap.get(cv2.CAP_PROP_FPS)

fourcc = cv2.VideoWriter_fourcc(*'MP4V')
videoWriter = cv2.VideoWriter('C:\\Users\\matt2\Desktop\\bs\\video.mp4', fourcc, fps, (int(width),int(height)))

ret, frame = cap.read()

print(width, height, fps)

while (ret):
    ret, frame = cap.read()
    cv2.imshow('video', frame)
    videoWriter.write(frame)
 
    if cv2.waitKey(1) == 27:
        break
 
cap.release()
videoWriter.release()
cv2.destroyAllWindows()