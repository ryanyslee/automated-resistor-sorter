import pandas as pd
import numpy as np
from collections import Counter
import time
import os

"""
===============================================================================
KNN Weight Optimizer (Full-Grid Search)
===============================================================================
DESCRIPTION:
A machine learning optimization script that computationally determines the 
ideal Hue, Saturation, and Value (HSV) weights for the KNN classifier based 
on the specific lighting conditions of the hardware "Black Box".

CORE FUNCTIONALITY:
1. Grid Search: Iterates through hundreds of HSV multiplier combinations.
2. Vectorized Math: Uses NumPy matrix operations to rapidly calculate 
   weighted Euclidean distances across the entire state space.
3. LOOCV: Evaluates each weight combination using Leave-One-Out Cross-
   Validation to find the absolute maximum classification accuracy.
===============================================================================
"""


# 1. Load Data
print("Loading dataset...")
df = pd.read_csv(os.path.join("training_dataset", 'knn_data_final_final_pruned.csv'))

# Drop the gold tolerance band
df = df[df['Label'].str.lower() != 'gold']

# Normalize the HSV data to 0.0 - 1.0
points_norm = df[['H', 'S', 'V']].values / np.array([179.0, 255.0, 255.0])
labels = df['Label'].values
N = len(labels)

# 2. Define the Search Space (The numbers we want to test)
# We will test combinations of H(3.0 to 10.0), S(0.5 to 4.0), and V(0.5 to 4.0)
W_H_options = np.arange(3.0, 10.0, 0.2) 
W_S_options = np.arange(0.4, 4.0, 0.2)
W_V_options = np.arange(0.4, 4.0, 0.2)

total_combos = len(W_H_options) * len(W_S_options) * len(W_V_options)
print(f"Starting Grid Search on {total_combos} combinations...")
start_time = time.time()

best_accuracy = 0.0
best_weights = (0, 0, 0)
K = 7 

# 3. The Grid Search Loop
for w_h in W_H_options:
    for w_s in W_S_options:
        for w_v in W_V_options:
            
            correct_predictions = 0
            weights = np.array([w_h, w_s, w_v])
            
            # Leave-One-Out Cross-Validation
            for i in range(N):
                target_point = points_norm[i]
                target_label = labels[i]
                
                # Fast Vectorized distances against all points simultaneously
                diffs = np.abs(points_norm - target_point)
                
                # Hue wrap-around logic (0.99 and 0.01 are only 0.02 apart)
                hue_diffs = diffs[:, 0]
                mask = hue_diffs > 0.5
                hue_diffs[mask] = 1.0 - hue_diffs[mask]
                diffs[:, 0] = hue_diffs
                
                # Apply the current experimental weights and calculate Euclidean distance
                # weighted_sq_diffs = (diffs * weights) ** 2
                # distances = np.sqrt(np.sum(weighted_sq_diffs, axis=1))
                
                # New Manhattan Distance
                distances = np.sum(diffs * weights, axis=1)
                
                # Set distance to self as infinity so it can't vote for itself
                distances[i] = np.inf 
                
                # Get the top K nearest neighbors
                nearest_indices = np.argpartition(distances, K)[:K]
                top_k_labels = labels[nearest_indices]
                
                # Take a vote
                prediction = Counter(top_k_labels).most_common(1)[0][0]
                
                if prediction == target_label:
                    correct_predictions += 1
                    
            # Calculate final accuracy for this weight combination
            accuracy = (correct_predictions / N) * 100
            
            # If this is the best combo we've seen, save and print it
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_weights = (w_h, w_s, w_v)
                print(f"New Best! W_H: {w_h:.1f}, W_S: {w_s:.1f}, W_V: {w_v:.1f}  --> Acc: {accuracy:.2f}%")

print(f"\n Grid Search completed in {time.time() - start_time:.1f} seconds.")
print("====================================")
print("🏆 OPTIMAL WEIGHTS")
print("====================================")
print(f"Hue Weight (W_H) : {best_weights[0]:.1f}")
print(f"Sat Weight (W_S) : {best_weights[1]:.1f}")
print(f"Val Weight (W_V) : {best_weights[2]:.1f}")
print(f"Maximum Accuracy : {best_accuracy:.2f}%")