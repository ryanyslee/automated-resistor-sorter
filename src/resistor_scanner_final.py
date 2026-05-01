import cv2
import numpy as np
import csv
import math
from collections import Counter
import os
import time

"""
===============================================================================
Autonomous Resistor Identification System (CV + KNN)
===============================================================================
DESCRIPTION:
Processes images of singulated E12 resistors in a controlled "Black Box" 
environment to autonomously calculate resistance in Ohms. 

CORE PIPELINE:
1. Segmentation & Cropping: Isolates and mathematically flattens the 
   resistor body using OpenCV morphological operations.
2. KNN Classification: Identifies color bands using a custom, grid-search 
   optimized K-Nearest Neighbors model in a weighted HSV state space.
3. Spatial Sequencing: Determines the correct reading direction by measuring 
   physical edge-to-band pixel gaps, completely bypassing tolerance bands.
4. Majority Voting: Cross-references multiple horizontal scan lines to 
   output a highly robust, final Ohms calculation.
===============================================================================
"""

class ResistorKNN:
    def __init__(self, csv_file, k):
        self.k = k
        self.training_data = [] 
        self.training_labels = []
        
        # Ranges for normalization (Standard OpenCV HSV ranges)
        self.MAX_VALS = np.array([179.0, 255.0, 255.0])
        
        self.load_data(csv_file)
        
        # Multipliers/digits dictionaries (Same as before)
        self.MULTIPLIERS = {
            'black': 1, 'brown': 10, 'red': 100, 'orange': 1000, 
            'yellow': 10000, 'green': 100000, 'blue': 1000000
        }
        self.COLOR_TO_DIGIT = {
            'black': 0, 'brown': 1, 'red': 2, 'orange': 3, 'yellow': 4,
            'green': 5, 'blue': 6, 'violet': 7, 'grey': 8
        }

        # self.weights = (6.4, 1.0, 3.2) # final_pruned
        self.weights = (3.0, 1.4, 2.8)

        self.DEBUG_MODE = False # set to False to silence debug outputs

    def normalize(self, h, s, v):
        """ Normalize HSV values to range [0.0, 1.0] """
        return np.array([h, s, v]) / self.MAX_VALS

    def load_data(self, csv_file):
        try:
            with open(csv_file, 'r') as file:
                reader = csv.reader(file)
                next(reader, None) # Skip header
                
                self.training_data = []
                self.training_labels = []
                
                for row in reader:
                    if not row: continue
                    h, s, v = int(row[0]), int(row[1]), int(row[2])
                    label = row[3]
                    
                    # NORMALIZE TRAINING DATA IMMEDIATELY
                    norm_point = self.normalize(h, s, v)
                    
                    self.training_data.append(norm_point)
                    self.training_labels.append(label)
                    
            print(f"KNN Loaded: {len(self.training_data)} Normalized points.")
            
        except Exception as e:
            print(f"Error loading CSV: {e}")

    def predict_pixel(self, h, s, v):
        if not self.training_data: 
            print("Error: KNN Data is missing.")
            return None
        
        # Normalizing the input pixel (to match the normalized training data)
        norm_input = self.normalize(h, s, v)
        h_input, s_input, v_input = norm_input

        # Defining importance weights (For Euclidean)
        W_H = self.weights[0]  # largest weight to Hue (actual color)
        W_S = self.weights[1]  # next important is saturation
        W_V = self.weights[2]  # value doesn't distinguish b/w colors (so least important)
        
        # Weights for Manhattan

        distances = []
        for i, train_point in enumerate(self.training_data):
            h_train, s_train, v_train = train_point
            
            # Hue Wrap-Around (on 0.0-1.0 scale)
            # Ex. Distance between 0.99 (Red) and 0.01 (Red) is 0.02, not 0.98
            diff_h = abs(h_input - h_train)
            if diff_h > 0.5: 
                diff_h = 1.0 - diff_h
            
            diff_s = abs(s_input - s_train)
            diff_v = abs(v_input - v_train)

            # Weighted Euclidean
            # dist = math.sqrt((diff_h * W_H)**2 + (diff_s * W_S)**2 + (diff_v * W_V)**2)
            
            # Manhattan Distance
            dist = diff_h * W_H + diff_s * W_S + diff_v * W_V
            
            # Appends the weighted Euclidean and the corresponding color labels
            distances.append((dist, self.training_labels[i]))
        
        # Sorts the tuples by increasing Euclidean order 
        # If there is a tie, the one that was found first wins
        distances.sort(key=lambda x: x[0])
        nearest_neighbors = distances[:self.k]
        
        # List of length K with top labels
        labels = [n[1] for n in nearest_neighbors]
        # .most_common(1) gives you something like [('red'), 3]
        prediction = Counter(labels).most_common(1)[0][0]
        
        # vote_weights = {}
        
        # for dist, label in nearest_neighbors:
        #     weight = 1.0 / ((dist ** 2) + 0.00001)
        #     if label in vote_weights:
        #         vote_weights[label] += weight
        #     else:
        #         vote_weights[label] = weight
        
        # prediction = max(vote_weights.items(), key=lambda x: x[1])[0]
        
        return prediction
    
    def scan_resistor(self, roi_image, mode):
        """ Acts as a switchboard to route the image to the correct algorithm """
        if roi_image is None or roi_image.size == 0:
            print("Error: Empty ROI image passed to scanner.")
            return None
        
        if mode == "horizontal":
            print("Identifying resistor...")
            return self._scan_horizontal_2(roi_image)
    
    def _scan_single_line(self, hsv_roi, y, margin, width):
        """ Scans a single horizontal row and returns the detected color sequence and gaps. """
        pixel_row = hsv_roi[y, margin : width - margin]
        
        detected_bands = []
        prev_color = "beige"
        count = 0
        block_start_x = margin
        
        for i, pixel in enumerate(pixel_row[::2]):
            real_x = margin + (i * 2)
            h, s, v = pixel
            
            # Predict using KNN
            color = self.predict_pixel(h, s, v)
            if color == "gold":
                color = "beige"
        
            consecutive_threshold = 5
            
            if color == prev_color:
                count += 1
            else:
                if count >= consecutive_threshold:
                    detected_bands.append((prev_color, block_start_x, real_x - 1))
                prev_color = color
                block_start_x = real_x
                count = 1
        
        if count >= consecutive_threshold:
            detected_bands.append((prev_color, block_start_x, width - margin - 1))

        # Merge neighbors
        merged_bands = []
        if detected_bands:
            current_band = detected_bands[0]
            for next_band in detected_bands[1:]:
                if next_band[0] == current_band[0]:
                    current_band = (current_band[0], current_band[1], next_band[2])
                else:
                    merged_bands.append(current_band)
                    current_band = next_band
            merged_bands.append(current_band)
                    
        # Remove all instances of "beige" and "gold"
        valid_bands = [blocks for blocks in merged_bands if blocks[0] not in ["beige", "gold"]]

        if len(valid_bands) > 0:
            color_sequence = tuple([bands[0] for bands in valid_bands])
            left_gap = valid_bands[0][1]
            right_gap = width - valid_bands[-1][2]
            return {
                "sequence": color_sequence,
                "left_gap": left_gap,
                "right_gap": right_gap
            }
            
        return None
    
    def _scan_horizontal(self, roi_image):
        """ Identifies bands using KNN prediction per pixel """
        hsv_roi = cv2.cvtColor(roi_image, cv2.COLOR_BGR2HSV)
        height, width, _ = hsv_roi.shape
        
        center_y = height // 2
        
        # Scan 1-D vectors (5-line analysis)
        # offset = height // 8
        # scan_y_coords = [center_y, center_y - offset, center_y + offset,
        #                  center_y - offset*2, center_y + offset*2]
        
        # For 3-line analysis
        offset = height // 4
        scan_y_coords = [center_y, center_y - offset, center_y + offset]

        # Ignore the left/right 15% of the image to avoid the tapered ends
        margin = int(width * 0.12) 

        all_detected_sequences = []

        for y in scan_y_coords:
            # Drawing analyzed 1-D vectors for visualization
            # Overall lines in red
            cv2.line(roi_image, (0, y), (width, y), (0, 0, 255), 1)
            # Actual pixels of reference in green
            cv2.line(roi_image, (margin, y), (width - margin, y), (0, 255, 0), 2)
            
            detected_sequence = self._scan_single_line(hsv_roi, y, margin, width)
            if detected_sequence:
                all_detected_sequences.append(detected_sequence)
       
        if not all_detected_sequences:
            print("Error: No Bands Detected!")
            return None  
        
        for i, item in enumerate(all_detected_sequences):
            print(f'Sequence {i + 1}', item["sequence"])
        
        valid_scans = [item for item in all_detected_sequences if len(item["sequence"]) == 3]
        
        if not valid_scans:
            print("Error: No scan lines detected a complete 3-band sequence.")
            return None
    
        # Vote on the color sequence only
        sequences_only = [item["sequence"] for item in valid_scans]
        vote_counts = Counter(sequences_only)
        
        # Get all top results
        max_votes = vote_counts.most_common(1)[0][1]
        
        # List of sequences with the most votes
        # ex. [('Red', 'Black', 'Red'), ('Orange', 'Black', 'Red')]
        tied_winners = [seq for seq, count in vote_counts.items() if count == max_votes]
        
        if len(tied_winners) > 1:
            print(f"Tie Detected between: {tied_winners}")
            winner_sequence = tied_winners[0]
        else:
            winner_sequence = tied_winners[0]
        
        # Retrieving the first horizontal line that correctly classified the sequence
        winning_data = next(item for item in all_detected_sequences if item["sequence"] == winner_sequence)
        print(f"Left Gap: {winning_data['left_gap']}, Right Gap: {winning_data['right_gap']}")
        
        final_bands = list(winner_sequence)
        
        if winning_data["right_gap"] < winning_data["left_gap"]:
            final_bands.reverse()
        
        # List of all detected colors (Expect 4)    
        print(f"Final Sequence: {final_bands}")
        return self.calculate_resistance(list(final_bands))
    
    # Utilizes "Deep Scan" for risky false positives
    def _scan_horizontal_2(self, roi_image):
        """ Identifies bands using KNN prediction per pixel """
        hsv_roi = cv2.cvtColor(roi_image, cv2.COLOR_BGR2HSV)
        height, width, _ = hsv_roi.shape
        
        center_y = height // 2
        # For 3-line analysis
        offset = height // 4
        # Ignore the left/right 15% of the image to avoid the tapered ends
        margin = int(width * 0.08)
        
        scanned_y_coords = []
        all_detected_sequences = []
        winner_sequence = None
        
        # PHASE 1: Standard 3-Line Scan
        phase1_y_coords = [center_y, center_y - offset, center_y + offset]

        for i,y in enumerate(phase1_y_coords):
            scanned_y_coords.append(y)
            result = self._scan_single_line(hsv_roi, y, margin, width)
            
            if result:
                self.dprint(f"Sequence {i+1} (Y-coord: {y}): {result['sequence']}")
            
                # Only count lines that found exactly 3 bands
                if len(result["sequence"]) == 3:
                    all_detected_sequences.append(result)
            else:
                self.dprint(f"Sequence {i+1} (Y-coord: {y}): No valid bands detected")
            
        if all_detected_sequences:
            sequences_only = [item["sequence"] for item in all_detected_sequences]
            vote_counts = Counter(sequences_only).most_common()
            
            # Check for Fast Path: 2 out of 3 votes
            if len(vote_counts) > 0 and vote_counts[0][1] >= 2:
                winner_sequence = vote_counts[0][0]
                self.dprint(f"Phase 1 Pass! Winner: {winner_sequence}")
                
        # PHASE 2: Deep Scan Trigger (2 new lines)
        if not winner_sequence:
            self.dprint("\nAmbiguous Read!!! Triggering Deep Scan...")
            phase2_y_coords = [center_y - (offset // 2), center_y + (offset // 2)]
            
            for i, y in enumerate(phase2_y_coords):
                scanned_y_coords.append(y)
                result = self._scan_single_line(hsv_roi, y, margin, width)
                
                if result:
                    self.dprint(f"Sequence {i+4} (Y-coord: {y}): {result['sequence']}")

                    # Only count lines that found exactly 3 bands
                    if len(result["sequence"]) == 3:
                        all_detected_sequences.append(result)
                
                else:
                    self.dprint(f"Sequence {i+4} (Y-coord: {y}): No valid bands detected")
            
            # Drawing analyzed 1-D vectors for visualization
            for y in scanned_y_coords:
                # Overall lines in red
                cv2.line(roi_image, (0, y), (width, y), (0, 0, 255), 1)
                # Actual pixels of reference in green
                cv2.line(roi_image, (margin, y), (width - margin, y), (0, 255, 0), 2)       
                    
            # Phase 2 Final Voting Check
            if all_detected_sequences:
                sequences_only = [item["sequence"] for item in all_detected_sequences]
                vote_counts = Counter(sequences_only).most_common()
                
                # Check for Deep Path: 3 out of 5 votes
                if len(vote_counts) > 0 and vote_counts[0][1] >= 3:
                    winner_sequence = vote_counts[0][0]
                    self.dprint(f"✅ Phase 2 Pass! {winner_sequence} achieved 3/5 consensus")
                else:
                    self.dprint(f"❌ Reject: No consensus after Deep Scan. Votes: {vote_counts}")
                    return None
            else:
                self.dprint("❌ Reject: No valid 3-band sequences detected across 5 lines.")
                return None
                  
        # Retrieving the first horizontal line that correctly classified the sequence
        winning_data = next(item for item in all_detected_sequences if item["sequence"] == winner_sequence)
        self.dprint(f"Left Gap: {winning_data['left_gap']}, Right Gap: {winning_data['right_gap']}")
        
        final_bands = list(winner_sequence)
        
        if winning_data["right_gap"] < winning_data["left_gap"]:
            final_bands.reverse()
        
        # Print final band sequence 
        print(f"Final Sequence: {final_bands}")
        return self.calculate_resistance(list(final_bands))
        
    def _scan_vertical(self, roi_image):
        """ Identifies bands using a Column-Sweep (Vertical Squeegee) Method """
        hsv_roi = cv2.cvtColor(roi_image, cv2.COLOR_BGR2HSV)
        height, width, _ = hsv_roi.shape
        
        # Ignore the left/right 15% to avoid the tapered wire ends
        margin = int(width * 0.15) 
        
        # Define 5 vertical sampling points (20%, 35%, 50%, 65%, 80% down the resistor)
        # This completely avoids the dark shadows at the very top/bottom edges
        y_samples = [
            int(height * 0.20),
            int(height * 0.24),
            int(height * 0.28),
            int(height * 0.32),
            int(height * 0.36),
            int(height * 0.40),
            int(height * 0.44),
            int(height * 0.48),
            int(height * 0.52),
            int(height * 0.56),
            int(height * 0.60),
            int(height * 0.64),
            int(height * 0.68),
            int(height * 0.72),
            int(height * 0.76),
            int(height * 0.80),
        ]

        # Draw our sampling lines on the image for debugging/visualization
        for y in y_samples:
            cv2.line(roi_image, (margin, y), (width - margin, y), (0, 0, 255), 1)

        column_colors = []

        # SWEEP ACROSS THE X-AXIS
        for x in range(margin, width - margin):
            vertical_votes = []
            
            # At each X column, sample the 5 Y points
            for y in y_samples:
                h, s, v = hsv_roi[y, x]
                color = self.predict_pixel(h, s, v)
                vertical_votes.append(color)
                
            # What is the statistical mode of this vertical column?
            # e.g., ['gold', 'gold', 'white_glare', 'gold', 'beige'] -> 'gold'
            winning_column_color = max(set(vertical_votes), key=vertical_votes.count)
            column_colors.append((winning_column_color, x))

        # GROUP CONSECUTIVE COLUMNS INTO BANDS
        blocks = []
        current_color = column_colors[0][0]
        consecutive_count = 0
        
        # Because our columns are vertically verified, we only need a color 
        # to survive for 2 consecutive X-pixels to be considered a real band!
        consecutive_threshold = 5
        
        for color, x in column_colors:
            if color == current_color:
                consecutive_count += 1
            else:
                # If the block ended, check if it was thick enough and NOT the background
                if consecutive_count >= consecutive_threshold:
                    blocks.append(current_color)
                
                # Reset for the new color
                current_color = color
                consecutive_count = 3
                
        # Catch the final block at the end of the loop
        if consecutive_count >= consecutive_threshold:
            blocks.append(current_color)

        # MERGE ADJACENT BLOCKS (Just in case a gap split a single band in two)
        # e.g., [Yellow, Yellow, Gold] -> [Yellow, Gold]
        merged_bands = []
        if blocks:
            merged_bands.append(blocks[0])
            for color in blocks[1:]:
                if color != merged_bands[-1]:
                    merged_bands.append(color)
        
        final_bands = [color for color in merged_bands if color != "beige"]

        print(f"Detected Sequence: {final_bands}")
        
        if not final_bands:
            return "No Bands Detected"
            
        return self.calculate_resistance(final_bands)

    def calculate_resistance(self, bands):
        """ (Same logic as previous script) """
        if len(bands) < 3: 
            print(f"Incomplete Read: {bands}")
            return None
        
        # Flip if Gold is first
        if bands[0] in ['gold', 'silver'] and bands[-1] not in ['gold', 'silver']:
            bands.reverse()
            
        try:
            d1 = self.COLOR_TO_DIGIT.get(bands[0], 0)
            d2 = self.COLOR_TO_DIGIT.get(bands[1], 0)
            mult = self.MULTIPLIERS.get(bands[2], 1)
            # tol = bands[-1] if len(bands) > 3 else "None"
            
            ohms = (d1 * 10 + d2) * mult
            
            if ohms >= 1_000_000: val = f"{ohms/1_000_000:g}M"
            elif ohms >= 1_000: val = f"{ohms/1_000:g}K"
            else: val = f"{ohms:g}"
            
            return f"{val} Ohms"
        
        except Exception as e:
            print(f"Error: {e}")
            return None
        
    def dprint(self, *args, **kwargs):
        "Custom print function that only executes if DEBUG_MODE is True."
        if self.DEBUG_MODE:
            print(*args, **kwargs)

def extract_horizontal_resistor(frame, contour):
    '''Mathematically flattens a slanted resistor and crops it.'''
    rect = cv2.minAreaRect(contour)
    (x_c, y_c), (w, h), angle = rect

    # ensure width is the long side so the resistor is horizontal
    if w < h:
        angle += 90
        w, h = h, w
        
    # Get rotation matrix and rotate the full frame
    M = cv2.getRotationMatrix2D((x_c, y_c), angle, 1.0)
    rotated_frame = cv2.warpAffine(frame, M, (frame.shape[1], frame.shape[0]))
    
    # Crop the exact rectangle out of the rotated frame
    x_crop = max(0, int(x_c - w/2))
    y_crop = max(0, int(y_c - h/2))
    
    cropped_resistor = rotated_frame[y_crop:y_crop+int(h), x_crop:x_crop+int(w)]
    return cropped_resistor

def get_resistor_contours(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Hardcoded mask for beige
    lower_beige = np.array([20, 100, 110])
    upper_beige = np.array([35, 255, 255]) 
    
    
    raw_mask = cv2.inRange(hsv, lower_beige, upper_beige)
    
    # cv2.imshow("1. Raw HSV Mask (Notice the wire noise)", raw_mask)
    
    noise_kernel = np.ones((25, 3), np.uint8)
    opened_mask = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, noise_kernel)
    
    # cv2.imshow("2. After OPENING (Wire noise should be gone)", opened_mask)
    
    # Connecting masks that are close to each other horizontally
    kernel_width = 100 # larger width bridges wider gaps
    kernel_height = 20
    bridge_kernel = np.ones((kernel_height, kernel_width), np.uint8)
    closed_mask = cv2.morphologyEx(opened_mask, cv2.MORPH_CLOSE, bridge_kernel)
    
    # cv2.imshow("3. After CLOSING (Solid Resistor Body)", closed_mask)
    
    # Draws an invisible vector outline around the outermost edges of the white resistor blob
    contours, _ = cv2.findContours(closed_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    return contours

def main():
    # Initialize KNN Engine
    # knn = ResistorKNN(os.path.join("training_dataset", "knn_data_pruned_7.csv"), k=7)
    # knn = ResistorKNN(os.path.join("training_dataset", "knn_data_baseline.csv"), k=9)
    # knn = ResistorKNN(os.path.join("training_dataset", "knn_data_final_base.csv"), k=7)
    # knn = ResistorKNN(os.path.join("training_dataset", "knn_data_final_pruned_3.csv"), k=5)
    knn = ResistorKNN(os.path.join("Full_System", "knn_data_final_pruned_3.csv"), k=5)

    # Load image
    test_resistor = os.path.join("final_test", "120_ohm_2.jpg")
    test_resistor = "test_resistor.jpg"
    # test_resistor = os.path.join("edge_cases", "two_resistors_2.jpg")
    
    start_time = time.perf_counter()
    
    frame = cv2.imread(test_resistor)
    
    contours = get_resistor_contours(frame)
    
    total_area = sum(cv2.contourArea(c) for c in contours)
    print(f"Contour Area: {total_area}")
    
    if len(contours) > 1 or total_area > 30000.0:
        print(f"Error: More than one resistor was detected")
        return None

    if len(contours) == 0:
        print("Error: No resistor present within frame")
        return None
    
    c = contours[0]
   
    # 1. Use the new function to perfectly flatten and crop the resistor
    resistor_body = extract_horizontal_resistor(frame, c)
    
    # 2. Draw the rotated bounding box on the original frame
    rect = cv2.minAreaRect(c)
    box = cv2.boxPoints(rect)
    box = np.int32(box)
    cv2.drawContours(frame, [box], 0, (0, 255, 0), 2)
    
    # 3. Analyze the perfectly flat, cropped resistor body
    result = knn.scan_resistor(resistor_body, mode="horizontal")
    # result = knn.scan_resistor(resistor_body, mode="vertical")
    print("Resistance: ", result)
    
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Identification Time: {elapsed_time:.4f} seconds")
    
    cv2.imshow("Cropped & Flattened ROI", resistor_body)
    cv2.putText(frame, result, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Scanner", frame)
        
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    

# --- MAIN ---
if __name__ == "__main__":
    main()
