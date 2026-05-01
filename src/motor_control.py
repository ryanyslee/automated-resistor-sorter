from pyfirmata2 import Arduino, util
from pynput.keyboard import Key, Controller
import time
import json

keyboard = Controller()

UP_ANGLE_TOP = 45;
UP_ANGLE_BOTTOM = 77;
DOWN_ANGLE_TOP = 0;
DOWN_ANGLE_BOTTOM = 25; 
TRAPDOOR_OPEN = 20; 
SPEED = 1; 

# Default values for bins
bins = ["100 Ohms", "220 Ohms", "330 Ohms", "470 Ohms", "1K Ohms", "2.2K Ohms", "3.3K Ohms", "4.7K Ohms", "10K Ohms", "22K Ohms", "33K Ohms", "47K Ohms", "Incomplete Read", "220K Ohms", "1M Ohms"]
angles = [3, 53, 95, 135, 173]

# Init Arduino pins
board = Arduino('/dev/ttyACM0')
time.sleep(2)
top_flap = board.get_pin('d:6:s')
bottom_flap = board.get_pin('d:7:s')
tower_rotation = board.get_pin('d:8:s')
singulation_speed = board.get_pin('d:3:p')
trapdoor = board.get_pin('d:9:s')
leds = board.get_pin('d:4:o')
vibration = board.get_pin('d:2:o')

# Set all motors to default p  osition
top_flap.write(DOWN_ANGLE_TOP)
bottom_flap.write(DOWN_ANGLE_BOTTOM)
trapdoor.write(0)
vibration.write(0)
tower_rotation.write(angles[2]) # center
singulation_speed.write(0)
leds.write(0)

def vibrate():
	vibration.write(1)
	time.sleep(0.5)
	vibration.write(0)

def update_bin_values():
	# Open and load the JSON file
    with open('resistor_values.json', 'r') as file:
        data = json.load(file)
		# Convert ints in json to strings to match CV output
        for i in range(1, 16):
            if i != 13: # Bin 13 always "Incomplete Read"
                value = data[str(i)]
                if value >= 1_000_000: ohm = f"{value/1_000_000:g}M Ohms"
                elif value >= 1000: ohm = f"{value/1000:g}K Ohms"
                else: ohm = f"{value:g} Ohms" # This format matches CV output
                bins[i-1] = ohm
		
def singulation_on():
	singulation_speed.write(SPEED)

def singulation_off():
	singulation_speed.write(0)
	
def LEDs_on():
	leds.write(1)
	
def LEDs_off():
	leds.write(0)

def rotate_tower(angle):
	tower_rotation.write(angle)

def raise_bottom_flap():
	bottom_flap.write(UP_ANGLE_BOTTOM)
	
def raise_trapdoor():
	trapdoor.write(TRAPDOOR_OPEN)
	time.sleep(0.3)
	trapdoor.write(0)

def raise_top_flap():
	top_flap.write(UP_ANGLE_TOP)

def lower_bottom_flap():
	bottom_flap.write(25)

def lower_top_flap():
	top_flap.write(0)
	
def motor_exit():
	leds.write(0)
	singulation_speed.write(0)
	board.exit()

def set_position(value):
	
	global i
	
	if not value:
		with open('cv_output.json', "w") as f:
			json.dump({1: "Error", 2: "moving to Reject Bin"}, f)
		# notify UI to read new value
		keyboard.press('r')
		keyboard.release('r')
		return
	
	if value in bins:
		i = bins.index(value)
		value = "Resistor Value: " + value[:-5] + "\u03A9"
		with open('cv_output.json', "w") as f:
			json.dump({1: value, 2: f"moving to Bin {i+1}"}, f)
		# notify UI to read new value
		keyboard.press('r')
		keyboard.release('r')
	else:
		i = 12 # index of reject bin
		value = "Resistor Value: " + value[:-5] + "\u03A9"
		with open('cv_output.json', "w") as f:
			json.dump({1: value, 2: "no bin assigned, \nmoving to Reject Bin"}, f)
		keyboard.press('r')
		keyboard.release('r')

	level = (i // 5) # Level is 0, 1, or 2
	angle = angles[i % 5] # Angles index 0 through 4
			
	rotate_tower(angle)
	if level == 0:
		raise_top_flap()
	elif level == 1:
		raise_bottom_flap()
	# Else for bottem level 2 both ramps are down
		
def reset_position():
	# lower flaps
	lower_top_flap()
	lower_bottom_flap()
	# rotate to center
	rotate_tower(angles[2])
	
