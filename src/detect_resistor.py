import numpy as np
# AVG_VALUE = 80 # 89 with cap off
AVG_VALUE = 81.8 # With masking tape

def check_for_resistor(picam2):
    """Takes a single high-speed frame to check for presence."""
    try:
        # Grab frame directly from active stream RAM
        img = picam2.capture_array('main')
        if img is not None:
            avg_intensity = np.mean(img)
            # print(f"Intensity: {avg_intensity}")

            # If intensity > threshold, resistor is present
            if avg_intensity > AVG_VALUE:
                print(f'Intensity is ', avg_intensity)
                return True
    except Exception as e:
        print(f"Sensor error: {e}")
        
    return False
