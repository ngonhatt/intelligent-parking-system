# 🚗 Intelligent Parking System

## 📌 Overview
This project is an Intelligent Parking Management System implemented using
Arduino Nano, designed to automate vehicle entry and exit using RFID and
image processing.
The system combines microcontroller-based control, hardware actuation,
and a PC-based management interface.

---

## 🔧 System Components
- Arduino Nano (Main controller)
- RFID Reader
- USB Camera
- Servo Motor (Barrier control)
- Embedded controller
- PC-based monitoring software
- CSV / Excel files for vehicle data storage

---

## ⚙️ Features
- RFID card scanning for vehicle identification
- Automatic image capture on card scan
- License plate recognition
- Automatic and manual barrier control
- Vehicle entry and exit counting
- Registration and deregistration of parking cards
- Safety logic to prevent barrier closing when a vehicle is detected

---

## 🧠 System Workflow
1. RFID card is scanned
2. Arduino Nano sends vehicle ID to the PC via serial communication
3. PC application captures vehicle image from camera
4. System verifies vehicle registration
5. Barrier opens automatically if authorized
6. Vehicle count is updated
7. Barrier closes after vehicle passes


---

## 🛠️ Software & Tools
- Arduino (C / C++)
- Serial communication (Arduino ↔ PC)
- Image processing on PC
- PC-based control interface
- CSV and Excel-based data management

---

## 📷 Demo
* PARKING SYSTEM PROTOTYPE
  
<img width="471" height="419" alt="image" src="https://github.com/user-attachments/assets/fa523d43-e00a-4a7c-92da-c7b3e2618169" />

* USER INTERFACE (UI)

<img width="1179" height="613" alt="image" src="https://github.com/user-attachments/assets/5c05f8e5-f072-4dca-a1c9-789c8a3ced4e" />

* VEHICLE LICENSE PLATE CAPTURE SYSTEM AT ENTRY

<img width="1058" height="641" alt="image" src="https://github.com/user-attachments/assets/210d8086-00b7-4dd9-ac32-94af039e0cda" />

* VEHICLE LICENSE PLATE CAPTURE SYSTEM AT EXIT

<img width="1037" height="627" alt="image" src="https://github.com/user-attachments/assets/2f1527fa-28a7-4d4b-9569-bdb9767e8ad7" />

* THE SYSTEM STORES VEHICLE ENTRY AND EXIT DATA INTO A CSV FILE AND EXCEL FILE 

<img width="566" height="223" alt="image" src="https://github.com/user-attachments/assets/adaf3b94-316f-44c1-911e-1b908e512273" />

<img width="604" height="292" alt="image" src="https://github.com/user-attachments/assets/e11fcbcc-a9b0-4496-9b59-224cb370f591" />


---

## 📚 What I Learned
- Arduino Nano-based system design
- RFID reader integration with microcontroller
- Serial communication between Arduino and PC
- Coordinating embedded firmware with PC software
- Designing real-world parking automation logic
- Implementing safety mechanisms in embedded systems

---

## 🚀 Future Improvements
- Replace CSV / Excel with database storage
- Improve license plate recognition accuracy
- Migrate from Arduino Nano to a more powerful MCU (e.g. ESP32 or STM32)
- Add cloud-based monitoring

## 🧠 Project Structure
```text
intelligent-parking-system/
├── arduino/        # Arduino Nano firmware
├── pc_app/         # Python PC application
└── README.md

