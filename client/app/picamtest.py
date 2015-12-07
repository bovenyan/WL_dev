import time
import picamera
import cv2
# import common
import sys
import getopt

with picamera.PiCamera() as camera:
	camera.resolution = (1920, 1080)
	time.sleep(2)
	camera.capture('test.jpg')

cap = cv2.VideoCapture(0)
cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 640)	
cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 480)

if cap is None or not cap.isOpened():
	print 'Warning: unable to open video source: 0'

shot_idx = 0
shotdir = '/home/pi/captured'
while True:
	imgs = []
	ret, img = cap.read()
	imgs.append(img)
	cv2.imshow('capture %d' % shot_idx, img)
	ch = 0xFF & cv2.waitKey(1)
	if ch == 27:
		break
	if ch == ord(' '):
		for i, img in enumerate(imgs):
			fn = '%s/shot_%d_%03d.bmp' % (shotdir, i, shot_idx)
			cv2.imwrite(fn, img)
			print fn, 'saved'
		shot_idx += 1
cv2.destroyAllWindows()