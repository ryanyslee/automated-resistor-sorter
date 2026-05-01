import os
import time
from enum import Enum
import cv2
from picamera2 import Picamera2
import threading
from pynput.keyboard import Key, Controller
import gc

# Timers: first wait 30s til trying vibration motor
# After first resistor, wait 10s til trying vibration motor
# After 10 s of pulsing vibration motor, give up and turn off

# Importing custom modules
from motor_control import singulation_off, singulation_on, LEDs_off, LEDs_on, raise_trapdoor, motor_exit, reset_position, set_position, update_bin_values, vibrate
from event_list import get_event, Events, add_event
from detect_resistor import check_for_resistor
from full_hardware_scanner import capture_image, analyze_image
from resistor_scanner_final import ResistorKNN
from main_ui import run_ui

# Hardware setup (Picam)
picam2 = Picamera2()
config = picam2.create_preview_configuration()
config['main']['size'] = (1000, 600)
picam2.configure(config)
picam2.start()
picam2.set_controls({
    "ScalerCrop": (1140, 1110, 1000, 600),
    "AeEnable": False, 
    "ExposureTime": 30000 # Adjust this if image is too dark/bright
})

time.sleep(1) # Camera stabilization

# ID configuration
IMAGE_PATH = "current_scan.jpg"
KNN_CSV_PATH = "knn_data_final_final_pruned.csv"
knn = ResistorKNN(KNN_CSV_PATH, k=5)
update_bin_values()

# Set up file to store pics of failed resistor cases for debugging
failed_cases_path = "/home/oso/Pictures/Captures/failed_resistors"
os.makedirs(failed_cases_path, exist_ok=True)

# Start UI as a background thread
thread = threading.Thread(target=run_ui)
thread.start()

# States of main state machine
class States(Enum):
	RUNNING = 1
	WAITING = 2
	TRYING_VIBRATION = 3
	
current_state = States.WAITING

# Start timer
update_time = time.perf_counter()
keyboard = Controller()
wait_time = 30
done = False

def state_machine():
	currEvent = get_event()
	
	global current_state, update_time, keyboard, done
 
	match current_state:
		case States.RUNNING:
			if currEvent == Events.PAUSE_PRESS:
				# Turn off motors and LEDs
				LEDs_off()
				singulation_off()
				current_state = States.WAITING
				update_time = time.perf_counter() # start timer
			elif currEvent == Events.RESISTOR_DETECTED:
				# Turn off singulation
				singulation_off()
				wait_time = 10
				# Run identification
				time.sleep(0.7) # tune time to let resistor settle
				update_time = time.perf_counter() # Reset timer
			
				if capture_image(picam2, IMAGE_PATH):
					resistance_value = analyze_image(knn, IMAGE_PATH)
					if resistance_value:
						print(f"Result Calculated: {resistance_value}")
						set_position(resistance_value)
						time.sleep(0.5)
						raise_trapdoor()
						singulation_on()
						time.sleep(1)
						reset_position()
					else:
						print("Error! Failed case")
						timestamp = time.strftime("%Y%m%d-%H%M%S")
						filename = f"image_{timestamp}.jpg"
						failed_resistors_path = os.path.join(failed_cases_path, filename)
						# capture image of fail
						capture_image(picam2, failed_resistors_path)
						set_position(None) # to notify UI
						raise_trapdoor()
						singulation_on()
						time.sleep(1.5)
			elif currEvent == Events.TIME_OUT:
				current_state = States.TRYING_VIBRATION
				wait_time = 5 
				update_time = time.perf_counter()
				
		case States.TRYING_VIBRATION:
			vibrate()
			time.sleep(0.5)
			if currEvent == Events.TIME_OUT:
				current_state = States.WAITING
				# signal to ui
				keyboard.press('t')
				keyboard.release('t')
				singulation_off()
				LEDs_off()
			elif currEvent == Events.RESISTOR_DETECTED:
				current_state = States.RUNNING
				wait_time = 10
				update_time = time.perf_counter()
			elif currEvent == Events.PAUSE_PRESS:
				current_state = States.WAITING
				keyboard.press('t')
				keyboard.release('t')
				singulation_off()
				LEDs_off()
				
		case States.WAITING:
			# TODO: add Events.
			if currEvent == Events.PLAY_PRESS:
				# Turn on motors and LEDs
				singulation_on()
				LEDs_on()
				current_state = States.RUNNING
				update_time = time.perf_counter()
			elif currEvent == Events.DONE:
				done = True
			elif currEvent == Events.UPDATE_VALUES:
				update_bin_values()
				#continue # call function from motor_control
				
def main():
	global update_time, done, wait_time
	try:
		while not done:
			# Check for events
			current_time = time.perf_counter()
			if (current_state == States.RUNNING or current_state == States.TRYING_VIBRATION ) and (current_time - update_time > wait_time):
				add_event(Events.TIME_OUT)

			if check_for_resistor(picam2):
				update_time = time.perf_counter()
				add_event(Events.RESISTOR_DETECTED)
			# Run state machine
			state_machine()
	finally:
		# Safety shutdown protocol
		print('Executing Safety Shutdown Protocol...')
		try:
			picam2.stop()
			picam2.close()
			camera.close()
			gc.collect()
			
		except Exception as e:
			pass
		time.sleep(1)
		motor_exit()
		print(f'Exiting...')

if __name__ == "__main__":
    main()

	

