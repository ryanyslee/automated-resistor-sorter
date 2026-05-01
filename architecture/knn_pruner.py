import csv
import math
import random
import os

W_H = 3.0 # 6.4
W_S = 1.2 # 1.0
W_V = 3.8 # 3.2

def circular_hue_diff(h1, h2):
    raw_diff = abs(int(h1) - int(h2))
    return min(raw_diff, 180 - raw_diff)

def manhattan_distance(p1, p2):
    dh = circular_hue_diff(p1[0], p2[0])
    ds = abs(int(p1[1]) - int(p2[1]))
    dv = abs(int(p1[2]) - int(p2[2]))
    return (W_H * dh) + (W_S * ds) + (W_V * dv)

# 1. Load the reinforced dataset
data = []
dataset_path = os.path.join("training_dataset", "knn_data_final_final_base.csv")
with open(dataset_path, "r") as f:
    reader = csv.DictReader(f)
    headers = reader.fieldnames
    for row in reader:
        data.append({
            'H': int(row['H']),
            'S': int(row['S']),
            'V': int(row['V']),
            'Label': row['Label'],
            'Original': row
        })

boundary_points = []
interior_points = []
k = 7

print("Pruning dataset... this may take a moment.")

# 2. Evaluate every single point to find the boundaries
for i, target in enumerate(data):
    distances = []
    for j, neighbor in enumerate(data):
        if i == j:
            continue
        dist = manhattan_distance((target['H'], target['S'], target['V']), 
                                  (neighbor['H'], neighbor['S'], neighbor['V']))
        distances.append((dist, neighbor['Label']))
    
    # Sort to find the K-nearest neighbors
    distances.sort(key=lambda x: x[0])
    top_k = distances[:k]
    
    # Check if this point is deep inside a cluster
    # Returns a single Boolean value (True if every pair matches)
    all_match = all(label == target['Label'] for _, label in top_k)
    
    if not all_match:
        boundary_points.append(target['Original'])
    else:
        interior_points.append(target['Original'])

# 3. Keep 10% of the interior points as "Gravity Anchors"
random.seed(42) # For consistent results
anchors = random.sample(interior_points, int(len(interior_points) * 0.30))

final_dataset = boundary_points + anchors

# 4. Save the highly optimized dataset
pruned_path = os.path.join("training_dataset", 'knn_data_final_final_pruned.csv')
with open(pruned_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(final_dataset)

print(f"Original Size: {len(data)} points")
print(f"Boundary Points Kept: {len(boundary_points)}")
print(f"Interior Anchors Kept: {len(anchors)}")
print(f"Final Pruned Size: {len(final_dataset)} points")