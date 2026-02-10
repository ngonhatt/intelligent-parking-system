#include <Servo.h>
#include <MFRC522.h>
#include <SPI.h>
  
#define SS_PIN1  8  // ESP32 pin GPIO32
#define SS_PIN2  10  // ESP32 pin GPIO33
#define RST_PIN 9   // ESP32 pin GPIO4

Servo servo_1;  // create servo object to control a servo
Servo servo_2;
MFRC522 rfid1(SS_PIN1, RST_PIN);  // Khởi tạo module 1
MFRC522 rfid2(SS_PIN2, RST_PIN);  // Khởi tạo module 2

MFRC522::PICC_Type piccType1, piccType2;

int servoPin_1 = A0;
int servoPin_2 = A1;   
int pir_1 = 2;                // Chân cho cảm biến PIR1
int pir_2 = 3;                // Chân cho cảm biến PIR2
int angle_1 = 0; 
int angle_2 = 0;   
int current_angle_1 =0;   
int current_angle_2 =0;  
int pirState_1;
int pirState_2;
void setup() {
  Serial.begin(9600);
  servo_1.attach(servoPin_1);  // attaches the servo on pin 9 to the servo object
  servo_2.attach(servoPin_2);    // Gắn servo vào chân
  servo_1.write(angle_1);         // Đặt góc ban đầu cho servo
  servo_2.write(angle_2);         // Đặt góc ban đầu cho servo
  pinMode(pir_1, INPUT);       // Chân cảm biến PIR1
  pinMode(pir_2, INPUT);       // Chân cảm biến PIR2
  pinMode(SS_PIN1, OUTPUT);  // Thiết lập chân SS cho module 1
  pinMode(SS_PIN2, OUTPUT);  // Thiết lập chân SS cho module 2

  digitalWrite(SS_PIN1, HIGH);  // Vô hiệu hóa module 1 ban đầu
  digitalWrite(SS_PIN2, HIGH);  // Vô hiệu hóa module 2 ban đầu

  SPI.begin(); // Khởi tạo SPI bus
  rfid1.PCD_Init(); // Init MFRC522 module 1
  rfid2.PCD_Init(); // Init MFRC522 module 2

  Serial.println("Tap an RFID/NFC tag on the RFID-RC522 reader");
}
//PIR1
void PIR_1(){
    Serial.println("CO VAT CAN.");
    Serial.println("Motion detected! Opening servo to 90 degrees.");
    for (angle_1 = current_angle_1; angle_1 < 90; angle_1 += 1) { // Mở servo dần từ 0 đến 90 độ
    servo_1.write(angle_1);
    delay(10); // Delay nhỏ để servo di chuyển mượt mà
    }
}
//PIR2
void PIR_2(){
    Serial.println("CO VAT CAN.");
    Serial.println("Motion detected! Opening servo to 90 degrees.");
    for (angle_2 = current_angle_2; angle_2 < 90; angle_2 += 1) { // Mở servo dần từ 0 đến 90 độ
    servo_2.write(angle_2);
    delay(10); // Delay nhỏ để servo di chuyển mượt mà
    }
}

void openservo1(){
      Serial.println("Received command to open servo.");
      for (angle_1 = 0; angle_1 < 90; angle_1 += 1) { // Mở servo dần từ 0 đến 90 độ
        servo_1.write(angle_1);
        delay(10); // Delay nhỏ để servo di chuyển mượt mà
      }
      Serial.println("Angle: " + String(angle_1));
}
//servo1
void closeservo1(){
      Serial.println("Received command to close servo.");
      Serial.println("Angle: " + String(angle_1));
      for (angle_1 = 90; angle_1 > 0; angle_1 -= 1) { // Đóng servo dần từ 90 đến 0 độ
        servo_1.write(angle_1);
        current_angle_1 = angle_1;
        delay(40); // Delay nhỏ để servo di chuyển mượt mà
        pirState_1 = digitalRead(pir_1);
      if (pirState_1 == LOW) { // Kiểm tra ngay lập tức nếu có vật cản
       PIR_1();
       break; // Ngưng di chuyển nếu có vật cản
      }
      }
      Serial.println("Angle: " + String(angle_1));
}
//servo2
void openservo2(){
      Serial.println("Received command to open servo.");
      for (angle_2 = 0; angle_2 < 90; angle_2 += 1) { // Mở servo dần từ 0 đến 90 độ
        servo_2.write(angle_2);
        delay(10); // Delay nhỏ để servo di chuyển mượt mà
      }
      Serial.println("Angle: " + String(angle_2));
}

void closeservo2(){
      Serial.println("Received command to close servo.");
      Serial.println("Angle: " + String(angle_2));
      for (angle_2 = 90; angle_2 > 0; angle_2 -= 1) { // Đóng servo dần từ 90 đến 0 độ
        servo_2.write(angle_2);
        current_angle_2 = angle_2;
        delay(40); // Delay nhỏ để servo di chuyển mượt mà
        pirState_2 = digitalRead(pir_2);
      if (pirState_2 == LOW) { // Kiểm tra ngay lập tức nếu có vật cản
       PIR_2();
       break; // Ngưng di chuyển nếu có vật cản
      }
      }
      Serial.println("Angle: " + String(angle_2));
}
void handleCommand(char command) {
  if (command == '1') {  // Lệnh mở servo đến 90 độ
    openservo1();
  } else if (command == '2') {  // Lệnh đóng servo về 0 độ
    closeservo1();
  }
  else if (command == '3') {  // Lệnh đóng servo về 0 độ
    openservo2();
  }
  else if (command == '4') {  // Lệnh đóng servo về 0 độ
    closeservo2();
  }

}

void serialEvent() {
  while (Serial.available() > 0) {
    char command = Serial.read();  // Đọc lệnh từ cổng Serial
    handleCommand(command);        // Xử lý lệnh
  }
}

void loop() {
  // Quét module 1
  digitalWrite(SS_PIN1, LOW);  // Kích hoạt module 1
  digitalWrite(SS_PIN2, HIGH); // Vô hiệu hóa module 2
  
  // Bắt đầu giao dịch SPI cho module 1
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0)); // Đặt các thông số SPI cho module 1
  if (rfid1.PICC_IsNewCardPresent()) {
    if (rfid1.PICC_ReadCardSerial()) {
      piccType1 = rfid1.PICC_GetType(rfid1.uid.sak);
      

      Serial.print("@");
      for (int i = 0; i < rfid1.uid.size; i++) {
        Serial.print(rfid1.uid.uidByte[i] < 0x10 ? "0" : "");
        Serial.print(rfid1.uid.uidByte[i], HEX);
      }
      Serial.println();
    }
  }
  rfid1.PICC_HaltA(); // Halt PICC
  rfid1.PCD_StopCrypto1(); // Stop encryption on PCD
  SPI.endTransaction(); // Kết thúc giao dịch SPI cho module 1
  digitalWrite(SS_PIN1, HIGH);  // Vô hiệu hóa module 1 sau khi quét xong

  // Quét module 2
  digitalWrite(SS_PIN1, HIGH);  // Vô hiệu hóa module 1
  digitalWrite(SS_PIN2, LOW);   // Kích hoạt module 2
  
  // Bắt đầu giao dịch SPI cho module 2
  SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE0)); // Đặt các thông số SPI cho module 2
  if (rfid2.PICC_IsNewCardPresent()) {
    if (rfid2.PICC_ReadCardSerial()) {
      piccType2 = rfid2.PICC_GetType(rfid2.uid.sak);
      

      Serial.print("&");
      for (int i = 0; i < rfid2.uid.size; i++) {
        Serial.print(rfid2.uid.uidByte[i] < 0x10 ? "0" : "");
        Serial.print(rfid2.uid.uidByte[i], HEX);
      }
      Serial.println();
    }
  }
  rfid2.PICC_HaltA(); // Halt PICC
  rfid2.PCD_StopCrypto1(); // Stop encryption on PCD
  SPI.endTransaction(); // Kết thúc giao dịch SPI cho module 2
  digitalWrite(SS_PIN2, HIGH);  // Vô hiệu hóa module 2 sau khi quét xong

  // Thêm một chút thời gian chờ
  delay(50); // 0.5s
}
