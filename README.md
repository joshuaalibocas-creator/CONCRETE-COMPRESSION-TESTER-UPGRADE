
JABIASR Automated Concrete Compression Machine Interface


User Manual & Technical Operation Guide

This software suite controls and monitors automated concrete compression testing systems. It interfaces directly with local instrumentation platforms via high-speed serial links, providing real-time metric visualization, interactive load plotting, and automated test data compliance logging.

🛠️ System Prerequisites & Installation


Option 1: Standalone Application (compressionapp.exe)

For field use on laptops without Python installed:
1. Navigate to the Releases section on this GitHub repository page.
2. Download the latest version of compressionapp.exe.
3. Move the file to any preferred folder or create a desktop shortcut.
4. No installation required—double-click to execute instantly.

Option 2: Running from Source (Thonny / Development)

If running the raw source files, install the required layout and telemetry drivers via the package manager or terminal:
bash
pip install matplotlib pyserial
Use code with caution.

🚀 Step-by-Step Operating Instructions


1. Hardware Connections & Setup

1. Connect the machine's control board to your laptop using a standard USB interface cable.
2. Power on the machine console.
3. Launch compressionapp.exe.
4. In the top-right corner, select the active connection link from the COM Port dropdown menu.
5. Click Connect. The system control actions will change from disabled to active.

2. Enter Specimen Identification Metrics

Before starting a compression test run, fill out the identification field parameters in the left-hand panel. This data is critical for structural validation logging:
• Client Name: The name of the client ordering the concrete strength verification breakdown.
• Site / Location: The physical structural pour point or project location site.
• Weight (kg): The precise weight of the concrete test cylinder in kilograms.
• Batch Code: The unique batch tracking code identifying the mixed truck or load delivery.

3. Select Display Metrics

• Use the Display Unit dropdown menu to switch between kn (Kilonewtons) and lbf (Pounds-Force).
• You can switch this at any time before, during, or after the test run. The live metrics display and the vertical axis on the chart window will instantly rescale to match your choice.

4. Executing the Test Profile

1. Click TARE SCALE to zero out any initial line drift or static load offset.
2. Click START TEST RUN. This transmits the activation handshake to the Arduino controller.
3. The Test Sequence Execution:
	• The system smoothly ramps up the loading lines, displaying live force values on the chart plot.
	• At 500 kN, the hardware automatically holds the hydraulic line locked for 2 seconds to settle internal valve forces.
	• The loading automatically resumes until it hits 1200 kN, where it holds steadily for 4 seconds.
	• The machine makes its final push towards the 1500 kN design ceiling limit.
4. Rupture & Auto-Save:
	• As soon as the material structural break occurs, the load crashes instantly back to zero on your screen.
	• The application automatically detects this compression failure drop, shuts off the motor outputs, and saves a structured file inside a folder named test results right next to your application.

5. Emergency Overrides

• If a sample misalignment or system pressure anomaly occurs, click the red STOP / ABORT button instantly. This safely drops all proportional valves and shuts off motor lines.

📊 File Storage & Data Records Structure

Every completed test run creates an automated comma-separated value record file named using the pattern: Test_[Date]_[Time]_[BatchCode].csv.
Files are saved automatically into the local test results/ folder. The output format logs structural properties down to millisecond increments:
csv
=== JABIASR COMPRESSION TEST RECORD ===
Timestamp,2026-10-30 16:23:45
Client,General Client
Site / Location,Site Alpha
Weight (kg),12.5
Batch Code,B-001
Peak Load Captured (kn),1500.00
Peak Load Captured (lbf),337213.4

Elapsed_Seconds,Load_kn,Load_lbf
0.000,0.00,0.0
0.050,2.00,449.6
...
Use code with caution.

🔧 Troubleshooting System Link Drops

• COM Port List is Empty: Click disconnect, unplug the USB hardware link from the computer, re-insert it firmly, restart the app, and check the dropdown again.
• Graph is Flat/Frozen: Verify the data stream transmission speed matches the required setting (115200 Baud Rate).
• Permission Errors on Export: Ensure the application folder is not inside a restricted Windows system path. Running the application out of your Documents/COMPRESSION directory guarantees safe local folder write permissions.
