import time
import cv2
import numpy as np
from gpiozero import LEDBoard
import os
from picamera2 import Picamera2

# Import KNN class and cropping function from the main script
from resistor_scanner_final import extract_horizontal_resistor, get_resistor_contours

def capture_image(picam2, image_path):
    """Quickly snaps an image using an already-running camera."""
    try:
        picam2.capture_file(image_path)
        # print("      📸 Image Captured...")
        return True
        
    except Exception as e:
        print(f"      ❌ Camera Error: {e}")
        return False
    

def analyze_image(knn, image_path):
    """Processes the image using the imported ResistorKNN model."""
    frame = cv2.imread(image_path)
    
    if frame is None:
        print(f"      ❌ Error: Could not load '{image_path}'.")
        return None

    contours = get_resistor_contours(frame)
    
    if len(contours) == 0 or not contours:
        print("       ❌ Error: No resistor found in the frame")
        return None
    
    total_area = sum(cv2.contourArea(c) for c in contours)
    # print(f"Contour Area: {total_area}")
    
    if len(contours) >= 2 or total_area > 30000.0:
        print(f"      ❌ Error: More than one resistor was detected")
        return None
    
    c = contours[0]
        
    resistor_body = extract_horizontal_resistor(frame, c)
    
    # Result: the actual resistance in ohms or None
    result = knn.scan_resistor(resistor_body, mode="horizontal")
    
    return result

# def identify_resistor(picam2, knn, image_path):
#     if capture_image(picam2, image_path):
#         resistance_value = analyze_image(knn, image_path)
    
#     if resistance_value:
#         print(f"Result Calculated: {resistance_value}")
#     else:
#         print("Incomplete Read / No Bands Detected")
#         return None