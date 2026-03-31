# DIY Scanning Spectrometer

A homemade scanning spectrometer built from scratch to analyze light spectra. This project integrates custom-built hardware (using a modified DVD disk and an Arduino) with a software pipeline for real-time data acquisition and spectral analysis.

## 🛠 Hardware Setup

The physical setup is built using accessible components while demonstrating fundamental principles of optics and signal processing.

* **Light Source:** Halogen lamp
* **Diffraction Grating:** A piece of a standard DVD disk. The microscopic indents ("pits") in the plastic layer of the disk act as an excellent, low-cost diffraction grating.
* **Detector:** BPW34 Photodiode
* **Actuator:** Stepper motor to rotate the grating/detector and scan across different wavelengths (steps).
* **Microcontroller:** Arduino (reads the photodiode analog signal and controls the motor).

> **Physical Setup**
> ![IMG_20260306_133834](https://github.com/user-attachments/assets/033af719-d409-4a1a-a151-9233630818d9)


## 💻 Software Pipeline

The project is divided into three logical software components:

1. **Firmware (`arduino/`):** C++ code running on the Arduino. It steps the motor and simultaneously reads the voltage from the BPW34 photodiode, sending the raw data over the Serial port.
2. **Data Logger (`python/`):** A Python script using `pyserial` and `pandas`. It listens to the COM port, captures the real-time data stream, and saves it into structured CSV files.
3. **Analysis (`analysis/`):** Jupyter Notebooks utilizing `matplotlib` to process the raw data. The analysis includes smoothing the signal, calculating Transmittance, and deriving Absorbance.

## 📊 Results and Data Analysis

Below are the preliminary results obtained by scanning the spectrum of air (reference) and a green sample.

### 1. Raw Spectra
The raw intensity of light captured by the photodiode at different motor steps. The blue line represents the reference (Air), and the green line represents the Green Sample.
> ![photo_2026-03-31_07-24-00](https://github.com/user-attachments/assets/f384c5ca-e34c-4579-98d2-4f72a72f1214)


### 2. Transmittance Spectrum
Calculated by dividing the sample spectrum by the reference spectrum.
> ![photo_2026-03-25_09-09-48](https://github.com/user-attachments/assets/7fd3af4c-26b3-4b58-a209-d33af20f765a)


### 3. Absorbance Spectrum
Derived from the transmittance data, showing which specific wavelengths are absorbed by the green sample.
> ![photo_2026-03-25_09-10-19](https://github.com/user-attachments/assets/dd7db2ab-9942-4735-98d1-a25963b34daf)
