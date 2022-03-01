#recording not in "real time"

import cv2
 
cap = cv2.VideoCapture(0)

fps = cap.get(cv2.CAP_PROP_FPS)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)   # float `width`
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)  # float `height`

fourcc = cv2.VideoWriter_fourcc(*'XVID')
videoWriter = cv2.VideoWriter('C:\\Users\\matt2\Desktop\\bs\\video.avi', fourcc, fps, (int(width),int(height)))

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