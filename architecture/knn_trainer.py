import cv2
import numpy as np
import csv
import os


"""
===============================================================================
Interactive Data Collection & Labeling Tool
===============================================================================
DESCRIPTION:
A manual Computer Vision utility used to extract ground-truth training data 
directly from physical prototype images captured by the Raspberry Pi-Cam.

CORE FUNCTIONALITY:
1. Interactive UI: Utilizes OpenCV mouse-callback functions to allow the user 
   to click directly on specific color bands within an image.
2. Color Conversion: Automatically extracts the BGR pixel data at the clicked 
   coordinate and converts it to the HSV color space.
3. Hot-Swappable Labeling: Uses keyboard bindings to rapidly switch the active 
   classification label and sequentially append the data directly into the CSV.
===============================================================================
"""


IMAGE_FILE = os.path.join("final_final_train", "680_ohm_3.jpg")
CSV_FILE = os.path.join("training_dataset", "knn_data_final_final_base.csv")

# Global variables
image = None
current_label = "beige" # Default label
drawing = False

def save_to_csv(h, s, v, label):
    """ Appends a single data point to the CSV file """
    file_exists = os.path.isfile(CSV_FILE)
    
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        # Write header if new file
        if not file_exists:
            writer.writerow(["H", "S", "V", "Label"])
        
        writer.writerow([h, s, v, label])
        print(f"Saved: H={h}, S={s}, V={v} -> Label: {label}")

def click_event(event, x, y, flags, params):
    global image, current_label
    
    if event == cv2.EVENT_LBUTTONDOWN:
        # Get Pixel Data
        b, g, r = image[y, x]
        pixel_array = np.uint8([[[b, g, r]]])
        hsv_pixel = cv2.cvtColor(pixel_array, cv2.COLOR_BGR2HSV)
        h, s, v = hsv_pixel[0][0]
        
        # Save to File
        save_to_csv(h, s, v, current_label)
        
        # Visual Feedback (Draw a circle of the label color)
        # Simple map for visual feedback color
        display_colors = {
            'black': (0,0,0), 'brown': (19,69,39), 'red': (0,0,255), 
            'orange': (0,165,255), 'yellow': (0,255,255), 'green': (0,255,0),
            'blue': (255,0,0), 'violet': (238,130,238), 'grey': (128,128,128),
            'white': (255,255,255), 'gold': (0,215,255), 'silver': (192,192,192),
            'beige': (180, 200, 240)
        }
        bgr_feedback = display_colors.get(current_label, (0, 255, 0))
        cv2.circle(image, (x, y), 2, bgr_feedback, -1)
        cv2.circle(image, (x, y), 3, (255, 255, 255), 1) # White border
        cv2.imshow("KNN Trainer", image)

def main():
    global image, current_label
    image = cv2.imread(IMAGE_FILE)
    
    if image is None:
        print(f"Error: Could not load {IMAGE_FILE}")
        return

    print("--- KNN DATA COLLECTOR ---")
    print("INSTRUCTIONS:")
    print("1. Press a key to select the color you are about to click.")
    print("2. Click on the image to save that pixel as a data point.")
    print("-" * 30)
    print("KEYS:")
    print(" [k] Black   [n] Brown   [r] Red")
    print(" [o] Orange  [y] Yellow  [g] Green")
    print(" [b] Blue    [v] Violet  [e] Grey")
    print(" [d] Gold    [SPACE] Beige (Body)")
    print(" [q] Quit")
    print("-" * 30)
    print(f"Current Label: {current_label.upper()}")

    cv2.imshow("KNN Trainer", image)
    cv2.setMouseCallback("KNN Trainer", click_event)

    while True:
        key = cv2.waitKey(0) & 0xFF
        
        # Label Switching Logic
        if   key == ord('k'): current_label = "black"
        elif key == ord('n'): current_label = "brown"
        elif key == ord('r'): current_label = "red"
        elif key == ord('o'): current_label = "orange"
        elif key == ord('y'): current_label = "yellow"
        elif key == ord('g'): current_label = "green"
        elif key == ord('b'): current_label = "blue"
        elif key == ord('v'): current_label = "violet"
        elif key == ord('e'): current_label = "grey"
        elif key == ord('d'): current_label = "gold"
        elif key == ord(' '): current_label = "beige"
        
        elif key == ord('q'): break
        
        print(f"Switched Label to: {current_label.upper()}")
        cv2.setWindowTitle("KNN Trainer", f"KNN Trainer - Label: {current_label.upper()}")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()