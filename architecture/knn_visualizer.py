import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import os


"""
===============================================================================
3D State-Space Data Visualizer
===============================================================================
DESCRIPTION:
A data visualization tool that renders the KNN training dataset in a 3D 
scatter plot to analyze color cluster overlaps and mathematical separation.

CORE FUNCTIONALITY:
1. Mathematical Warping: Applies the specific Hue, Saturation, and Value 
   weights to the raw data to show exactly how the algorithm "sees" the distance.
2. Filter Logic: Automatically isolates tolerance bands (Gold/Silver) to 
   analyze core resistance pigment overlaps.
3. Multi-View Rendering: Generates a 2x2 orthographic layout (Front, Side, 
   Top) to easily diagnose cluster collisions on specific axes (e.g., Hue vs Value).
===============================================================================
"""

# Load CSV data
df = pd.read_csv(os.path.join("training_dataset", "knn_data_final_final_pruned.csv"))

# Custom weights
W_H = 3.0
W_S = 1.4
W_V = 2.8

# Normalize and scale
df['H_weighted'] = (df['H'] / 179.0) * W_H
df['S_weighted'] = (df['S'] / 255.0) * W_S
df['V_weighted'] = (df['V'] / 255.0) * W_V

# Custom color mapping
color_map = {
    'black': 'black',
    'brown': 'saddlebrown',
    'red': 'red',
    'orange': 'darkorange',
    'yellow': 'gold',
    'green': 'green',
    'blue': 'blue',
    'violet': 'purple',
    'beige': '#d1bfae',
    'grey': 'grey'  
}

# Set up the 2x2 grid figure
fig = plt.figure(figsize=(18, 10))
fig.suptitle('Weighted KNN Space - 4 View Perspectives', fontsize=18, fontweight='bold')

# Define the 4 camera angles: (Elevation, Azimuth)
# Original default in matplotlib is roughly elev=30, azim=-60
views = [
    (30, -60),
    (20, -30),
    (15, -130),
    (60, -110)
]

# Loop through and create each subplot
for i in range(4):
    ax = fig.add_subplot(2, 2, i + 1, projection='3d')
    elev, azim= views[i]
    
    # Plot the data
    for label in df['Label'].unique():
        subset = df[df['Label'] == label]
        color = color_map.get(label.lower(), 'gray') 
        
        # Keeping your logic to exclude the "gold" tolerance band
        # if label.lower() == "gold" or label.lower() == "beige":
        #     ax.scatter(subset['H_weighted'], subset['S_weighted'], subset['V_weighted'], 
        #                c=color, label=label, s=30, edgecolors='black', alpha=0.8)
        
        if label.lower() != "gold":
            ax.scatter(subset['H_weighted'], subset['S_weighted'], subset['V_weighted'], 
                        c=color, label=label, s=30, edgecolors='black', alpha=0.8)

    # Labeling
    ax.set_xlabel('Weighted Hue (H)')
    ax.set_ylabel('Weighted Saturation (S)')
    ax.set_zlabel('Weighted Value (V)')
    
    # Set the camera angle
    ax.view_init(elev=elev, azim=azim)
    
    # Extract legend handles only from the first plot
    if i == 0:
        handles, labels = ax.get_legend_handles_labels()

# Place a single master legend on the right side of the entire figure
fig.legend(handles, labels, loc='center right', bbox_to_anchor=(0.98, 0.5), fontsize=12)

# Adjust layout to make room for the master legend
plt.tight_layout(rect=[0, 0, 0.9, 1]) 
plt.show()