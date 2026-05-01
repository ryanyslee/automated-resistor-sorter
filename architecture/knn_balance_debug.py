import csv
from collections import Counter
import os

"""
===============================================================================
Dataset Health & Imbalance Diagnostic Tool
===============================================================================
DESCRIPTION:
A diagnostic utility used to verify the statistical health and distribution 
of the physical training dataset before compiling the KNN model.

CORE FUNCTIONALITY:
1. Distribution Parsing: Reads the active CSV dataset and calculates the 
   share percentage of every color label.
2. Bias Detection: Automatically flags over-represented colors (>40% share) 
   that could cause the KNN to aggressively bias its voting.
3. Blindspot Detection: Flags under-represented colors (<5% share) that 
   risk becoming mathematically "invisible" in the 3D state space.
===============================================================================
"""

def analyze_training_data(csv_file):
    labels = []
    try:
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            next(reader) # Skip header
            for row in reader:
                if row: labels.append(row[3])
    except:
        print("Could not read CSV.")
        return

    # Count the balance
    counts = Counter(labels)
    total = len(labels)
    
    print(f"--- DATASET HEALTH CHECK (Total: {total}) ---")
    print(f"{'Color':<10} | {'Count':<5} | {'Share'}")
    print("-" * 30)
    
    for color, count in counts.most_common():
        share = (count / total) * 100
        status = "OK"
        if share > 40: status = "TOO MUCH (Bias Risk)"
        if share < 5:  status = "TOO LITTLE (Invisible)"
        
        print(f"{color:<10} | {count:<5} | {share:.1f}%  <-- {status}")

if __name__ == "__main__":
    # csv_file = os.path.join("training_dataset", "knn_data_final_base.csv")
    csv_file = os.path.join("training_dataset", "knn_data_final_final_pruned.csv")
    analyze_training_data(csv_file)