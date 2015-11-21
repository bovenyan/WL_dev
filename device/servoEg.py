# Script assumes the servo 0 conneccts to P1-7 header and servo 1 connects to P1-11 header
# Also, servo 0 controls panning (left/right) and servo 1 controls tilting (up/down)
from multiprocessing import Process, Queue
import time

# Upper limit
_Servo1UL = 100
_Servo0UL = 100

# Lower Limit
_Servo1LL = 35
_Servo0LL = 30


ServoBlaster = open('/dev/servoblaster', 'w')		# ServoBlaster is what we use to control the servo motors

Servo0CP = Queue()	# Servo zero current position, sent by subprocess and read by main process
Servo1CP = Queue()	# Servo one current position, sent by subprocess and read by main process
Servo0DP = Queue()	# Servo zero desired position, sent by main and read by subprocess
Servo1DP = Queue()	# Servo one desired position, sent by main and read by subprocess
Servo0S = Queue()	# Servo zero speed, sent by main and read by subprocess
Servo1S = Queue()	# Servo one speed, sent by main and read by subprocess


def P0():	# Process 0 controlles servo 0 that connects to P1-7 header
	speed = .1			# default speed
	_Servo0CP = 99		
	_Servo0DP = 100		
	while True:
		time.sleep(speed)
		if Servo0CP.empty():
			Servo0CP.put(_Servo0CP)	
		if not Servo0DP.empty():	
			_Servo0DP = Servo0DP.get()
		if not Servo0S.empty():			
			_Servo0S = Servo0S.get()	
			speed = .1 / _Servo0S		
		if _Servo0CP < _Servo0DP:					
			_Servo0CP += 1							
			Servo0CP.put(_Servo0CP)
			ServoBlaster.write('P1-7=' + str(_Servo0CP) + '\n')	#
			ServoBlaster.flush()
			if not Servo0CP.empty():				
				trash = Servo0CP.get()
		if _Servo0CP > _Servo0DP:
			_Servo0CP -= 1
			Servo0CP.put(_Servo0CP)
			ServoBlaster.write('P1-7=' + str(_Servo0CP) + '\n')	#
			ServoBlaster.flush()
			if not Servo0CP.empty():
				trash = Servo0CP.get()
		if _Servo0CP == _Servo0DP:
			_Servo0S = 1
			

def P1():	# Process 1 controlles servo 1 that connects to P1-11 header
	speed = .1
	_Servo1CP = 99
	_Servo1DP = 100
	while True:
		time.sleep(speed)
		if Servo1CP.empty():
			Servo1CP.put(_Servo1CP)
		if not Servo1DP.empty():
			_Servo1DP = Servo1DP.get()
		if not Servo1S.empty():
			_Servo1S = Servo1S.get()
			speed = .1 / _Servo1S
		if _Servo1CP < _Servo1DP:
			_Servo1CP += 1
			Servo1CP.put(_Servo1CP)
			ServoBlaster.write('P1-11=' + str(_Servo1CP) + '\n')
			ServoBlaster.flush()
			if not Servo1CP.empty():
				trash = Servo1CP.get()
		if _Servo1CP > _Servo1DP:
			_Servo1CP -= 1
			Servo1CP.put(_Servo1CP)
			ServoBlaster.write('P1-11=' + str(_Servo1CP) + '\n')
			ServoBlaster.flush()
			if not Servo1CP.empty():
				trash = Servo1CP.get()
		if _Servo1CP == _Servo1DP:
			_Servo1S = 1



Process(target=P0, args=()).start()	# Start the subprocesses
Process(target=P1, args=()).start()	#
time.sleep(1)				# Wait for them to start

def CamRight( distance, speed ):		# import ServoCtrl and call CamRight/Left/Up/Down with specified (distance,speed)
	global _Servo0CP					
	if not Servo0CP.empty():			
		_Servo0CP = Servo0CP.get()		
	_Servo0DP = _Servo0CP + distance	
	if _Servo0DP > _Servo0UL:			# Make sure it won't burn the servo!
		_Servo0DP = _Servo0UL			
	Servo0DP.put(_Servo0DP)				# Send the new desired position to the subprocess
	Servo0S.put(speed)					# Send the new speed to the subprocess
	return;

def CamLeft( distance, speed ):			
	global _Servo0CP
	if not Servo0CP.empty():
		_Servo0CP = Servo0CP.get()
	_Servo0DP = _Servo0CP - distance
	if _Servo0DP < _Servo0LL:
		_Servo0DP = _Servo0LL
	Servo0DP.put(_Servo0DP)
	Servo0S.put(speed)
	return;


def CamDown( distance, speed ):			
	global _Servo1CP
	if not Servo1CP.empty():
		_Servo1CP = Servo1CP.get()
	_Servo1DP = _Servo1CP + distance
	if _Servo1DP > _Servo1UL:
		_Servo1DP = _Servo1UL
	Servo1DP.put(_Servo1DP)
	Servo1S.put(speed)
	return;


def CamUp( distance, speed ):			
	global _Servo1CP
	if not Servo1CP.empty():
		_Servo1CP = Servo1CP.get()
	_Servo1DP = _Servo1CP - distance
	if _Servo1DP < _Servo1LL:
		_Servo1DP = _Servo1LL
	Servo1DP.put(_Servo1DP)
	Servo1S.put(speed)
	return;