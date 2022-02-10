import cv2
import numpy as np
 
# Turn on Laptop's webcam
cap = cv2.VideoCapture(0)


while True:
     
    ret, frame = cap.read()

    #float -> height + width of webcam
    width  = cap.get(3)
    height = cap.get(4)

    cv2.circle(frame, (320,240), 20, (30,40,30),4)
    # Locate points of the documents
    # or object which you want to transform

    #TL, TR, BR, BL
    pts1 = np.float32([[0, 0], [640, 0], [640, 480], [0, 480]])

    #TL, TR, BR, BL
    pts2 = np.float32([[0, 0], [640, 0], [640, 480], [0, 480]])
     
    # Apply Perspective Transform Algorithm
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    result = cv2.warpPerspective(frame, matrix, (int(width), int(height)))
     
    # Wrap the transformed image
    cv2.imshow('frame', frame) # Initial Capture
    cv2.imshow('frame1', result) # Transformed Capture
 
    if cv2.waitKey(24) == 27:
        break
 
cap.release()
cv2.destroyAllWindows()






# while True:

#     # # Here, I have used L2 norm. You can use L1 also.
#     # width_AD = np.sqrt(((pt_A[0] - pt_D[0]) ** 2) + ((pt_A[1] - pt_D[1]) ** 2))
#     # width_BC = np.sqrt(((pt_B[0] - pt_C[0]) ** 2) + ((pt_B[1] - pt_C[1]) ** 2))
#     # maxWidth = max(int(width_AD), int(width_BC))


#     # height_AB = np.sqrt(((pt_A[0] - pt_B[0]) ** 2) + ((pt_A[1] - pt_B[1]) ** 2))
#     # height_CD = np.sqrt(((pt_C[0] - pt_D[0]) ** 2) + ((pt_C[1] - pt_D[1]) ** 2))
#     # maxHeight = max(int(height_AB), int(height_CD))


#     # Apply Perspective Transform Algorithm
#     matrix = cv2.getPerspectiveTransform(pts1, pts2)
#     result = cv2.warpPerspective(frame, matrix, (500, 600))

#     # #compute a transformation matrix 
#     # matrix = cv2.getPerspectiveTransform(pts1, pts2)

#     # #apply transform matrix
#     # result = cv2.warpPerspective(frame, matrix, (500,500))
    

#     # Wrap the transformed image
#     cv2.imshow('frame', frame) # Initial Capture
#     cv2.imshow('frame1', matrix) # Transformed Capture
 
#     if cv2.waitKey(24) == 27:
#         break
 
# cap.release()
# cv2.destroyAllWindows()