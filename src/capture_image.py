import os
import time
import cv2
from picamera2 import Picamera2
from motor_control import LEDs_on, LEDs_off, raise_trapdoor

# Initialize LEDs
# leds = [LED(25), LED(23), LED(16), LED(26)]

# for led in leds: led.on()

LEDs_on()

time.sleep(1)

def capture_image(output_path, picam2):
    """
    Grabs a frame from the already-running preview stream.
    """
    # --- START TIMING HERE (After preview is already running) ---
    start_time = time.perf_counter()

    try:        
        # We specify 'main' to grab the current frame from the active stream
        # This avoids the "Still Mode" reconfiguration delay
        image_data = picam2.capture_array('main')

        # Convert RGB to BGR for OpenCV and save
        cv2.imwrite(output_path, cv2.cvtColor(image_data, cv2.COLOR_RGB2BGR))

        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        
        print(f"Capture + Save Success! Time: {elapsed_time:.4f} seconds")
        return image_data

    except Exception as e:
        print(f"An error occurred during capture: {e}")
        return None

if __name__ == "__main__":

    folder_path = "/home/oso/Pictures/Captures"
    os.makedirs(folder_path, exist_ok=True)

    # 1. Initialize Camera with PREVIEW config for speed
    picam2 = Picamera2()
    config = picam2.create_preview_configuration()
    
    # Set resolution
    config['main']['size'] = (1000, 600)
    picam2.configure(config)
    
    # 2. Start the stream BEFORE we try to capture
    picam2.start()
    
    # Apply crop and lock settings so it doesn't "hunt" for focus/exposure
    picam2.set_controls({
        "ScalerCrop": (1140, 1110, 1000, 600),
        "AeEnable": False, 
        "ExposureTime": 30000 # Adjust this if image is too dark/bright
    })

    # Give the camera a moment to stabilize the first frame
    time.sleep(1)

    try:
        # Turn all LEDs on
        #for led in leds: led.on()
        while True:
            user_input = input("\nPress [ENTER] to capture image (or 'q' to quit): ")
            if user_input.lower() == 'q':
                break

            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"image_fast_{timestamp}.jpg"
            full_save_path = os.path.join(folder_path, filename)

            print("Triggering instant capture...")
            img = capture_image(full_save_path, picam2)

            time.sleep(1)
            raise_trapdoor()

            if img is not None:
                print(f"Process complete. Array shape: {img.shape}")

            

    finally:
        # 3. Stop the stream only when the script is finished
        print("\nShutting down hardware safely...")
        picam2.stop()
        picam2.close()

        time.sleep(1)

        LEDs_off()
        
        # Turn all LEDs off
        #for led in leds: led.off()