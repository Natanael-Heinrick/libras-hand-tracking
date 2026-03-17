import cv2

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while True:
    ret, frame = camera.read()

    if not ret:
        print("Erro ao acessar webcam")
        break

    cv2.imshow("Webcam Test", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

camera.release()
cv2.destroyAllWindows()
