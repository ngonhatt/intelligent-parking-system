from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QGraphicsView, QGraphicsScene, QFileDialog
from PyQt5.QtGui import QImage, QPixmap,QFont
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal,QObject, pyqtSlot
from PyQt5.QtWidgets import *
from PyQt5 import uic 
import pandas as pd
import function.utils_rotate as utils_rotate
import function.helper as helper
import numpy as np
import cv2
import sys
import torch
import serial
import time
import os
from datetime import datetime, timedelta
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(device)

# Load YOLO models
yolo_LP_detect = torch.hub.load('yolov5', 'custom', path='model/LP_detector_nano_61.pt', force_reload=True, source='local').to(device)
yolo_license_plate = torch.hub.load('yolov5', 'custom', path='model/LP_ocr_nano_62.pt', force_reload=True, source='local').to(device)
yolo_license_plate.conf = 0.4

current = 0
class LicensePlateThread(QThread):
    plate_detected = pyqtSignal(dict)
    
    def __init__(self, frame, plate_id):
        super().__init__()
        self.frame = frame
        self.plate_id = plate_id
        
    def run(self):
        data = self.recognize_license_plate(self.frame)
        self.plate_detected.emit(data)    
    def recognize_license_plate(self, frame):
        global current
        data_dict = {'text': "unknown", 'image': None, 'id': self.plate_id}
        
        plates = yolo_LP_detect(frame, size=300)
        list_plates = plates.pandas().xyxy[0].values.tolist()
        if list_plates:
            for plate in list_plates:
                x, y, w, h = map(int, (plate[0], plate[1], plate[2] - plate[0], plate[3] - plate[1]))
                crop_img = frame[y:y+h, x:x+w]
                
                lp = ""
                for cc in range(2):
                    for ct in range(2):
                        lp = helper.read_plate(yolo_license_plate, utils_rotate.deskew(crop_img, cc, ct))
                        if lp != "unknown":
                            data_dict.update({'text': lp, 'image': crop_img})
                            break
                    if lp != "unknown":
                        break
        else: 
            data_dict['text']= "unknown"
        return data_dict

class CSVThread(QThread):
    result_Write = pyqtSignal(bool)
    result_Read = pyqtSignal(bool)  # Tín hiệu để truyền kết quả đọc

    def __init__(self, plate_number, plate_id, current_time, mode, csv_file='license_plates.csv'):
        super().__init__()
        self.plate_number = plate_number
        self.mode = mode  # Có thể là 'read' hoặc 'write'
        self.plate_id = plate_id
        self.csv_file = csv_file
        self.current_time = current_time

    def run(self):
        if self.mode == 'write':
            result = self.write_data_to_csv(self.plate_number, self.plate_id, self.current_time)
            self.result_Write.emit(result)
        elif self.mode == 'read':
            result = self.read_data_from_csv(self.plate_number, self.plate_id)
            self.result_Read.emit(result)

    def write_data_to_csv(self, lp, plate_id, current_time):
        global current
        if not plate_id:
            print("Plate ID is None or False, not writing to CSV.")
            return False
        else:
            df = pd.read_csv(self.csv_file, dtype={"plate_id": str})
            if plate_id in df["plate_id"].values:
                df.loc[df["plate_id"] == plate_id, "license_plate"] = str(lp)
                df.loc[df["plate_id"] == plate_id, "time"] = str(current_time)
                df.to_csv(self.csv_file, index=False)  # Thêm index=False để không ghi lại chỉ mục
                return True
            else:
                new_data = pd.DataFrame([[str(plate_id), str(lp), str(current_time)]], 
                                        columns=["plate_id", "license_plate","time"])
                df = pd.concat([df, new_data], ignore_index=True)
                new_data.to_csv(self.csv_file, mode='a', header=False, index=False)
                current =len(df)
                return True

    def read_data_from_csv(self, lp, plate_id):
        global current
        if not os.path.exists(self.csv_file):
            return False
        df = pd.read_csv(self.csv_file, dtype={"plate_id": str, "license_plate": str})
        if plate_id in df["plate_id"].values:
            matching_rows = df[df["plate_id"] == plate_id]
            if  not matching_rows.empty:
                stored_lp = matching_rows["license_plate"].values[0]
                if stored_lp == lp:
                    df.drop(matching_rows.index, inplace=True)
                    df.to_csv(self.csv_file, index=False)
                    current =len(df)
                    return True
                else:
                    return False
        else:
            return False 
class ExcelThread(QThread):
    result_Write = pyqtSignal(dict)
    result_Read = pyqtSignal(dict)  # Tín hiệu để truyền kết quả đọc
    result_Delete = pyqtSignal(dict)
    def __init__(self, HovaTen, Phone, plate_id, current_time, mode, excel_file='month.xlsx'):
        super().__init__()
        self.HovaTen = HovaTen
        self.Phone = Phone
        self.mode = mode  # Có thể là 'read' hoặc 'write'
        self.plate_id = plate_id
        self.excel_file = excel_file
        self.current_time = current_time

    def run(self):
        if self.mode == 'write':
            result = self.write_data_to_excel(self.HovaTen, self.Phone, self.plate_id, self.current_time)
            self.result_Write.emit(result)
        elif self.mode == 'read':
            result = self.read_data_from_excel(self.plate_id)
            self.result_Read.emit(result)
        elif self.mode == 'delete':
            result = self.delete_data_from_excel(self.HovaTen, self.Phone, self.plate_id)
            self.result_Delete.emit(result)

    def write_data_to_excel(self, HovaTen, Phone, plate_id, current_time):
        data_res = {'text': "Vui lòng thử lại", 'bool': False}
        if not plate_id:
            print("Plate ID is None or False, not writing to Excel.")
            return data_res
        else:
            if os.path.exists(self.excel_file):
                df = pd.read_excel(self.excel_file, dtype={"HovaTen": str, "Phone": str, "plate_id": str, "time": str})
            else:
                df = pd.DataFrame(columns=["HovaTen", "Phone", "plate_id", "time"])

            if plate_id in df["plate_id"].values:
                df.loc[df["plate_id"] == plate_id, "time"] = str(current_time)
            else:
                new_data = pd.DataFrame([[str(HovaTen),str(Phone),str(plate_id), str(current_time)]], 
                                        columns=["HovaTen", "Phone", "plate_id", "time"])
                df = pd.concat([df, new_data], ignore_index=True)
            data_res.update({'text': "Đăng ký thành công", 'bool': True})
            df.to_excel(self.excel_file, index=False, engine='openpyxl')  # Lưu file Excel
            return data_res

    def read_data_from_excel(self, plate_id):
        data_check = {'text': "Thẻ ngày", 'bool': False}
        if not os.path.exists(self.excel_file):
            return data_check
        
        # Đọc file Excel và chỉ định kiểu dữ liệu cho các cột
        df = pd.read_excel(self.excel_file, dtype={"plate_id": str, "time": str})
        
        # Kiểm tra xem plate_id có tồn tại trong file Excel không
        if plate_id in df["plate_id"].values :
            matching_rows = df[df["plate_id"] == plate_id]
            if not matching_rows.empty:
                stored_time_str = matching_rows["time"].values[0]
                stored_time = datetime.strptime(stored_time_str, "%d-%m-%Y - %H:%M:%S")  # Định dạng thời gian trong Excel
                if datetime.now() <= stored_time + timedelta(days=1):
                    data_check.update({'text': "Thẻ Tháng, Còn hạn!", 'bool': True})
                    return data_check
                else:
                    data_check.update({'text': "Thẻ Tháng, Hết hạn!", 'bool': True})
                    return data_check
        return data_check
    def delete_data_from_excel(self, HovaTen, Phone, plate_id):
        data_det = {'text': "Vui lòng thử lại", 'bool': False}
        if not os.path.exists(self.excel_file):
            print("Excel file does not exist. Nothing to delete.")
            return data_det

        # Đọc file Excel
        df = pd.read_excel(self.excel_file, dtype={"HovaTen": str, "Phone": str, "plate_id": str, "time": str})
        
        # Lọc theo tất cả các điều kiện: họ tên, số điện thoại, ID thẻ, biển số
        matching_rows = df[(df["HovaTen"] == HovaTen) & 
                        (df["Phone"] == Phone) & 
                        (df["plate_id"] == plate_id)]

        if not matching_rows.empty:
            # Xóa các dòng thỏa mãn điều kiện
            df.drop(matching_rows.index, inplace=True)
            # Lưu lại file Excel sau khi xóa
            df.to_excel(self.excel_file, index=False, engine='openpyxl')
            data_det.update({'text': "Hủy thành công", 'bool': True})
            return data_det
        else:
            data_det.update({'text': "Vui lòng thử lại", 'bool': False})
            return data_det
class SerialListener(QThread):
    data_available = pyqtSignal(str)  # Signal to emit data
    def __init__(self, serial_port,interval=10):
        super().__init__()
        self.serial_port = serial_port
        self.interval = interval
        self.running = True  # Flag to control the loop in run()

    def run(self):
        while self.running:
            if self.serial_port.in_waiting > 0:  # If there's data available
                data = self.serial_port.readline().decode('utf-8').strip()     
                self.data_available.emit(data)  # Emit data if available
            self.msleep(self.interval)  # Control the polling interval

    def stop(self):
        self.running = False
class SerialSender(QThread):
    def __init__(self, data, serial_port):
        super().__init__()
        self.data = data
        self.serial_port = serial_port
        self.running = True
        if not self.serial_port.is_open:
            self.serial_port.open()  # Mở cổng serial nếu chưa mở
    def run(self):
        if self.running:
            self.send_data(self.data)  # Gửi dữ liệu một lần
        self.stop()  # Dừng luồng sau khi gửi
    def send_data(self, data):
        if isinstance(data, str):
            data = data.encode()  # Convert to bytes if data is a string
        if self.serial_port.is_open:
            self.serial_port.write(data)  # Send data
    def stop(self):
        self.running = False
class Camera_Ui(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("bienso.ui", self)
        self.setWindowTitle("Camera")

        self.is_live = False

        self.graphicsView = self.findChild(QGraphicsView, "graphicsView")
        self.scene = QGraphicsScene(self)  
        self.graphicsView.setScene(self.scene)
        self.graphicsView.setStyleSheet("border: 5px solid black;")

        self.graphicsView_2 = self.findChild(QGraphicsView, "graphicsView_2")
        self.scene_2 = QGraphicsScene(self)  
        self.graphicsView_2.setScene(self.scene_2)
        self.graphicsView_2.setStyleSheet("border: 5px solid black;")

        self.capture = cv2.VideoCapture(2)
        self.capture_2 = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer_2 = QTimer()
        self.timer_2.timeout.connect(self.update_frame_2)
        
        self.btn_Live = self.findChild(QPushButton, "btn_Live")
        self.btn_Cap = self.findChild(QPushButton, "btn_Cap")
        self.btn_Check = self.findChild(QPushButton, "btn_Check")
        self.btn_Exit=self.findChild(QPushButton, "btn_Exit")
        self.label_BienSo = self.findChild(QLabel, "label_Bienso")
        self.label_BienSo_2 = self.findChild(QLabel, "label_Bienso_2")
        self.label = self.findChild(QLabel, "label")
        self.label_2 = self.findChild(QLabel,"label_2")
        self.label_5 = self.findChild(QLabel,"label_5")
        self.label_Time_In = self.findChild(QLabel,"label_Time_In")
        self.label_Time_Out = self.findChild(QLabel,"label_Time_Out")
        self.label_Quatity =  self.findChild(QLabel, "label_quatity")
        self.label_3 = self.findChild(QLabel,"label_3")
        self.label_4 = self.findChild(QLabel,"label_4")
        self.label_6 = self.findChild(QLabel,"label_6")
        self.label_7 = self.findChild(QLabel,"label_7")
        self.label_8 = self.findChild(QLabel,"label_8")
        self.label_9 = self.findChild(QLabel,"label_9")
        self.label_10 = self.findChild(QLabel,"label_10")
        self.label_11 = self.findChild(QLabel,"label_11")
        self.label_12 = self.findChild(QLabel,"label_12")
        self.label_month = self.findChild(QLabel, "label_month")
        self.lineEdit = self.findChild(QLineEdit,"lineEdit")
        self.lineEdit_2 = self.findChild(QLineEdit,"lineEdit_2")
        self.Action = self.findChild(QComboBox, "comboBox")
        self.Action.currentIndexChanged.connect(self.perform_action)  # Kết nối tín hiệu

        self.label_Time_In.setStyleSheet("border: 2px solid black;")
        self.label_Time_Out.setStyleSheet("border: 2px solid black;")
        self.label_Quatity.setStyleSheet("border: 2px solid black;")
        self.label_BienSo.setStyleSheet("border: 4px solid black;")
        self.label_BienSo_2.setStyleSheet("border: 4px solid black;")
        self.label.setStyleSheet("border: 2px solid black;")
        self.label_2.setStyleSheet("border: 2px solid black;") 
        self.label_month.setStyleSheet("border: 2px solid black;") 
        self.label_5.setPixmap(QPixmap("C:/Users/Win10/Desktop/Bienso/image_logo.png"))
        self.label_5.setScaledContents(True)

        self.btn_Live.clicked.connect(self.toggle_live)
        self.btn_Exit.clicked.connect(self.Exit)
        self.graphics_view_width = 0
        self.graphics_view_height = 0
        self.mode = 0
        self.license_plate_thread = None
        self.serial_sender = None
        self.csv_thread = None
        self.ExcelThread = None
        self.shared_serial_port = serial.Serial(port='COM7', baudrate=9600, timeout=1)
        global current
        current = len(pd.read_csv('license_plates.csv'))
        self.label_Quatity.setText(str(current))
        # Lưu kích thước gốc của cửa sổ và các widget
        self.original_window_size = self.size()
        self.original_sizes = {}
        self.original_fonts = {}
        self.original_positions = {}  # Lưu vị trí gốc

        self.widgets = [
            self.graphicsView,
            self.graphicsView_2,
            self.btn_Live,
            self.btn_Cap,
            self.btn_Check,
            self.btn_Exit,
            self.label_BienSo,
            self.label_BienSo_2,
            self.label,
            self.label_2,
            self.label_5,
            self.label_Time_In,
            self.label_Time_Out,
            self.label_Quatity,
            self.Action,
            self.label_9,
            self.label_8,
            self.label_7,
            self.label_6,
            self.label_4,
            self.label_3,
            self.label_10,
            self.label_11,
            self.label_12,
            self.lineEdit,
            self.lineEdit_2,
            self.label_month
        ]
        

        for widget in self.widgets:
            self.original_sizes[widget] = widget.size()
            self.original_fonts[widget] = widget.font().pointSize()
            self.original_positions[widget] = widget.pos()
        self.show()

    def resizeEvent(self, event):
        current_window_size = self.size()
        width_ratio = current_window_size.width() / self.original_window_size.width()
        height_ratio = current_window_size.height() / self.original_window_size.height()

        for widget in self.widgets:
            # Điều chỉnh kích thước widget
            original_size = self.original_sizes[widget]
            original_pos = self.original_positions[widget]

            new_width = int(original_size.width() * width_ratio)
            new_height = int(original_size.height() * height_ratio)

            new_x = int(original_pos.x() * width_ratio)
            new_y = int(original_pos.y() * height_ratio)

            widget.resize(new_width, new_height)
            widget.move(new_x, new_y)

            # Điều chỉnh font chữ
            if isinstance(widget, QLabel):  # Chỉ áp dụng font cho QLabel
                original_font_size = self.original_fonts[widget]
                new_font_size = int(original_font_size * min(width_ratio, height_ratio))
                widget.setFont(QFont("Arial", new_font_size))
            self.graphics_view_width = self.graphicsView.width()  # Hoặc graphics_view_2 tùy vào trường hợp
            self.graphics_view_height = self.graphicsView.height()
        super().resizeEvent(event)
    def perform_action(self):
        self.mode = self.Action.currentIndex()  # Lấy chế độ từ ComboBox
        print(self.mode)
        if self.mode == 0:  # Chế độ tự động
            self.btn_Cap.setEnabled(False)
            self.btn_Check.setEnabled(False)
            self.serial_sender = SerialSender(data = "mode_0", serial_port = self.shared_serial_port)
            self.serial_sender.start() 
            self.releaseThread(self.serial_sender)
            pass  
        elif self.mode == 1:  # Chế độ thủ công
            self.btn_Cap.setEnabled(True)
            self.btn_Check.setEnabled(True)
            self.btn_Cap.disconnect()  
            self.btn_Check.disconnect()
            self.serial_sender = SerialSender(data = "mode_1", serial_port = self.shared_serial_port)
            self.serial_sender.start() 
            self.releaseThread(self.serial_sender)
            self.btn_Cap.clicked.connect(lambda: self.sendData(id=True))
            self.btn_Check.clicked.connect(lambda: self.sendData(id=False))

    def sendData(self, id):
        if id:
            self.serial_sender = SerialSender(data = "ID_in", serial_port = self.shared_serial_port)
        else: 
            self.serial_sender = SerialSender(data = "ID_out", serial_port = self.shared_serial_port) 
        self.serial_sender.start() 
        self.serial_sender.wait()
        self.serial_sender.quit()  # Dừng luồng
        self.serial_sender= None 

    def toggle_live(self):
        if not self.is_live:
            self.is_live = True
            self.btn_Live.setText("STOP")
            self.capture = cv2.VideoCapture(2)
            self.capture_2 = cv2.VideoCapture(0)
            self.timer.start(30)
            self.timer_2.start(30)
        else:
            self.is_live = False
            self.btn_Live.setText("LIVE")
            self.timer.stop()
            self.timer_2.stop()
            self.scene.clear()
            self.scene_2.clear()
            self.capture.release()
            self.capture_2.release()
    def threadReadSerial(self):
        self.serial_listener = SerialListener(self.shared_serial_port)
        self.serial_listener.data_available.connect(self.start_processing_thread)
        self.serial_listener.start()
    @pyqtSlot(str)
    def start_processing_thread(self, data):
        plate_id = data[1:]  # This assumes the ID is directly after the '@'
        now = datetime.now().strftime('%d-%m-%Y - %H:%M:%S') 
        if data[0] == '@':
            if self.mode == 0 or self.mode == 1:
                self.capture_image(plate_id)
            elif self.mode == 2:
                self.ExcelThread = ExcelThread(self.lineEdit.text(), self.lineEdit_2.text(), plate_id, now, 
                                                mode='write', excel_file='month.xlsx')
                self.ExcelThread.result_Write.connect(self.Resgister)
                self.ExcelThread.start()               
            elif self.mode == 3:
                self.ExcelThread = ExcelThread(self.lineEdit.text(), self.lineEdit_2.text(), plate_id, now, 
                                                mode='delete', excel_file='month.xlsx')
                self.ExcelThread.result_Delete.connect(self.Resgister)
                self.ExcelThread.start()               
        elif data[0] == '&':
            self.check_license_plate(plate_id)
        else:
            print('Erorr')
    def capture_image(self,plate_id):
        if self.is_live:
            ret, frame = self.capture.read()
            if ret:
                start_time = time.perf_counter()  # Lấy thời gian bắt đầu
                # resized_frame = cv2.resize(frame, (300, 300))
                self.license_plate_thread = LicensePlateThread(frame, plate_id)
                self.license_plate_thread.plate_detected.connect(self.display_license_plate)
                self.license_plate_thread.start()
                end_time = time.perf_counter()  # Lấy thời gian kết thúc
                execution_time = end_time - start_time  # Tính thời gian xử lý
                print(f"Thời gian xử lý: {execution_time} giây")
    @pyqtSlot(dict)
    def display_license_plate(self, data): 
        global current
        now = datetime.now().strftime('%d-%m-%Y - %H:%M:%S') 
        if data['text'] != "unknown":
            self.label_Time_In.setText(now)
            self.label.setText(data['text'])
            self.update_label_with_color(data['image'], id=1)
            self.ExcelThread = ExcelThread(self.lineEdit.text(), self.lineEdit_2.text(), data['id'], now, 
                                               mode='read', excel_file='month.xlsx')
            self.ExcelThread.result_Read.connect(self.infor_Month)
            self.ExcelThread.start()
            self.csv_thread = CSVThread(data['text'], data['id'], now, mode='write',csv_file='license_plates.csv')
            self.csv_thread.result_Write.connect(self.threadSendDataWrite)
            self.csv_thread.start()               
        else:
            self.label.setText("No license plate")
            self.label_2.setStyleSheet("border: 2px solid black; color: red;")
            self.label_2.setText("Không có biển số!") 
            self.releaseThread(self.license_plate_thread)
    @pyqtSlot(dict)
    def infor_Month(self,data_check):
        if data_check['bool'] == True:
            self.label_month.setStyleSheet("border: 2px solid black; color: green;")
            self.label_month.setText(data_check['text'])
        else:
            self.label_month.setStyleSheet("border: 2px solid black; color: green;")
            self.label_month.setText(data_check['text'])
    @pyqtSlot(dict)
    def Resgister(self, data):
        if data['bool']:
            self.label_2.setStyleSheet("border: 2px solid black; color: green;")
            self.label_2.setText(data['text'])      
        else: 
            self.label_2.setStyleSheet("border: 2px solid black; color: red;")
            self.label_2.setText(data['text'])      
    @pyqtSlot(bool)
    def threadSendDataWrite(self, result):
        global current
        self.label_Quatity.setText(str(current))
        if result:
            self.label_2.setStyleSheet("border: 2px solid black; color: green;")
            self.label_2.setText("Mời vào!")
            self.serial_sender = SerialSender(data = "Open_in", serial_port = self.shared_serial_port) 
            self.serial_sender.start()      
        else: 
            self.label_2.setStyleSheet("border: 2px solid black; color: red;")
            self.label_2.setText("Vui lòng thử lại")
        self.releaseThread(self.serial_sender)
    def check_license_plate(self,plate_id):
        if self.is_live:
            ret, frame = self.capture_2.read()
            if ret:
                # resized_frame = cv2.resize(frame, (300, 300))
                self.license_plate_thread = LicensePlateThread(frame, plate_id)
                self.license_plate_thread.plate_detected.connect(self.handle_firebase_check)
                self.license_plate_thread.start()
    @pyqtSlot(dict)
    def handle_firebase_check(self, data):
        now = datetime.now().strftime('%d-%m-%Y - %H:%M:%S')
        if data['text'] != "unknown":
            self.label_Time_Out.setText(now)
            self.label.setText(data['text'])
            self.update_label_with_color(data['image'], id=2)
            self.ExcelThread = ExcelThread(self.lineEdit.text(), self.lineEdit_2.text(), data['id'], now, 
                                               mode='read', excel_file='month.xlsx')
            self.ExcelThread.result_Read.connect(self.infor_Month)
            self.ExcelThread.start()
            self.csv_thread = CSVThread(data['text'], data['id'], now, mode='read',csv_file='license_plates.csv')
            self.csv_thread.result_Read.connect(self.threadSendDataCheck)
            self.csv_thread.start()    
        else:
            self.label.setText("No license plate")
            self.label_2.setStyleSheet("border: 2px solid black; color: red;")
            self.label_2.setText("Không có biển số!")
        self.releaseThread(self.license_plate_thread)
    @pyqtSlot(bool)
    def threadSendDataCheck(self, result):
        global current
        self.label_Quatity.setText(str(current))
        if result:
            self.label_2.setStyleSheet("border: 2px solid black; color: green;")
            self.label_2.setText("Mời Ra!")
            self.serial_sender = SerialSender(data = "Open_out", serial_port = self.shared_serial_port) 
            self.serial_sender.start()
        else:
            self.label_2.setStyleSheet("border: 2px solid black; color: red;")
            self.label_2.setText("Vui lòng thử lại")  
        self.releaseThread(self.serial_sender) 
    def update_frame(self):
        ret, frame = self.capture.read()
        if ret:
            self.update_graphics_view(self.scene, frame)
    def update_frame_2(self):
        ret, frame = self.capture_2.read()
        if ret:
            self.update_graphics_view(self.scene_2, frame)
    def update_graphics_view(self, graphics_view, frame):
        view_width = self.graphics_view_width -10
        view_height = self.graphics_view_height -10
        
        resized_frame = cv2.resize(frame, (view_width, view_height), interpolation=cv2.INTER_AREA)
        h, w, ch = resized_frame.shape
        bytes_per_line = ch * w
        q_image = QImage(resized_frame.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        graphics_view.setSceneRect(0, 0, w, h)
        graphics_view.clear()
        graphics_view.addPixmap(QPixmap.fromImage(q_image))
    def update_label_with_color(self, color_image, id):
        label_size = self.label_BienSo.size()
        width = label_size.width()  # Lấy chiều rộng
        height = label_size.height()  # Lấy chiều cao
        color_image = cv2.resize(color_image, (width, height))
        if len(color_image.shape) == 3: 
            color_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
        h_color, w_color, _ = color_image.shape
        bytes_per_line_color = w_color * 3  
        q_image_color = QImage(color_image.data, w_color, h_color, bytes_per_line_color, QImage.Format_RGB888)
        pixmap_color = QPixmap.fromImage(q_image_color)
        if id == 1:
            self.label_BienSo.setPixmap(pixmap_color)
        elif id == 2:
            self.label_BienSo_2.setPixmap(pixmap_color)
    def releaseThread(self, thread):
        if thread is not None: 
            thread.wait()  
            thread.quit()  
            self.thread = None 
        else:
            print("Thread is already None or has not been started.")

    def Exit(self):
        repmess=QMessageBox.question(MainWindow,'Out', 'Bạn có chắc là muốn thoát Mainwindow?',QMessageBox.Yes|QMessageBox.No)
        if repmess==QMessageBox.Yes:
            self.capture.release()
            self.capture_2.release()
            app.exit()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    MainWindow = Camera_Ui()
    MainWindow.threadReadSerial()
    MainWindow.perform_action()
    MainWindow.show()
    sys.exit(app.exec_())
