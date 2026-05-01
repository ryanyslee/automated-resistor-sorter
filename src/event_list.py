from collections import deque
from enum import Enum

class Events(Enum):
    PLAY_PRESS = 1 # Play button pressed in UI
    PAUSE_PRESS = 2 # Pause button pressed in UI
    RESISTOR_DETECTED = 3 # PiCam registered resistor
    UPDATE_VALUES = 4 # User entered new bin values in UI
    TIME_OUT = 5 # 30 seconds have passed since resistor spotted
    DONE = 6
    

event_list = deque()

def get_event():
	if len(event_list) != 0:
		return event_list.popleft()
	else:
		return None
		
def add_event(event):
	event_list.append(event)
	
