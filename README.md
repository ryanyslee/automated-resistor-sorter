# Autonomous Resistor Sorter
An end-to-end autonomous mechatronic system designed to **singulate**, **identify**, and **sort** through-hole resistors from bulk input. This project integrates high-speed hardware control with a robust computer vision pipeline, achieving a **95% total system accuracy** and a **97.6% classification accuracy** with zero false positives.

## 🚀 Key Performance Metrics
- **Classification Accuracy:** 97.6% across 21 distinct resistance values.
- **Zero False Positives:** Intelligent edge-case handling ensures no resistor is ever missorted.
- **Inference Time:** ~1.80 seconds per component on edge hardware (Raspberry Pi).
- **Throughput:** Capable of processing 10+ resistor per minute.

## 🛠️ System Architecture
The respository is divided into two primary sections to separate real-time hardware execution from model development and optimization.

### 1. Real-Time Implementation (```/src```)
The software stack managing synchronized hardware operations.
- ```main.py```: The central state machine orchestrating the singulation, identification, and sorting lifecycle.
- ```motor_control.py```: PWM-driven GPIO control for the step-ladder singulation mechanism and the rotational storage tower.
- ```resistor_scanner_final.py```: The core classification engine utilizing a custom-weighted K-Nearest Neighbors (KNN) algorithm.
- ```detect_resistor.py```: Optical trigger using contour analysis to detect resistor entry and pause hardware for imaging.
- ```full_hardware_scanner.py```: Orchestrates high-resolution capture and coordinates data flow into KNN classifier.
- ```event_list.py```: Synchronized event hub that decouples hardware interrupts from the main logic loop.
- ```main_ui.py```: An asynchronous graphical user interface providing real-time system status and sorting results.

### 2. Architecture & Optimization (```/architecture```)
The development engine used to build and refine the classification logic.
- ```knn_trainer.py```: Interactive sampling tool used to manually extract HSV values from raw resistor images to build the training dataset.
- ```knn_balance_debug.py```: Statistical utility that calculates class distribution to ensure even representation across all color categories.
- ```knn_visualizer.py```: Generates 3D scatter plots in the HSV state space to evaluate color cluster separation and overlap.
- ```tune_weights.py```: Automates hyperparameter optimization through a grid search to determine the most accurate HSV scaling weights.
- ```knn_pruner.py```: Optimizes edge inference by removing redundant interior data points while preserving critical boundaries between color clusters.

## ⚙️ Hardware Stack
- **Primary Controller:** Raspberry Pi 4, managing high-level state machine logic and computer vision processing.
- **Peripheral Controller:** Arduino Uno, dedicated to low-level hardware control, including DC motor PWM for singulation and servo actuation for the storage tower.
- **Vision Subsystem:** Picamera2 housed in a custom "Black-Box" enclosure to ensure a controlled lighting environment.
- **Actuation & Lighting:**
  - **Singulation:** DC Motor-driven step-ladder mechanism.
  - **Storage:** Servo-actuated rotational tower with "multi-floor" delivery flaps.
  - **Illumination:** 4x LEDs for consistent color band identification.
 
## 🔧 Setup and Usage
**1. Clone the Repository:**
```bash
git clone https://github.com/your-username/resistor-sorter.git
cd resistor-sorter
```
**2. Hardware Configuration:** Ensure all GPIO pins are mapped according to the definitions in ```motor_control.py```.
**3. Run the System:**
```bash
python3 src/main.py
```

## 🎓 Project Context
This project was developed as part of the **Electromechanical Systems Design (24-671)** capstone at **Carnegie Mellon University**. The system was recognized for its technical excellence and design maturity, receiving a nomination for the university-wide **TechSpark Engineering Exposition**. It was ultimately honored with the **"Best Prototype"** award and was named **"Best Overall Project"** at the Mechanical Engineering Exposition.

**Team Members:** Hopewell Feldmann, Min Seo Kim, Ryan Lee, Katherene Qi, Ethan Steeg
