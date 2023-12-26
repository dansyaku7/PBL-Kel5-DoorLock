#include <Wire.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>
#include <ESP8266WiFi.h>
#include <SPI.h>
#include <MFRC522.h>
#include <ESP8266HTTPClient.h>
#include <PCF8574.h>

#define SS_PIN D4
#define RST_PIN D3
#define LED_G D0
#define RELAY D0
#define BUZZER D8
#define BUTTON_PIN 0
#define ACCESS_DELAY 2000
#define DENIED_DELAY 1000

MFRC522 mfrc522(SS_PIN, RST_PIN);

const char* ssid = "Queensa";
const char* password = "Mahira101010";
const char* flaskServerIp = "192.168.100.205";

struct AuthorizedCard {
  String uid;
  String name;
};

AuthorizedCard authorizedCards[3] = {
  {"5B4D4821", "Kelompok 5 PBL"},
  {"EF89D04E", "Abdan"},
  {"ADDEEDA5", "New User"}  // UID dan nama baru
};

WiFiClient wifiClient;

volatile bool buttonPressed = false;

void IRAM_ATTR buttonISR() {
  buttonPressed = true;
}

PCF8574 pcf8574(0x20);  // Alamat I2C PCF8574
hd44780_I2Cexp lcd(0x27, 2, 16);  // Alamat I2C LCD, 16x2 karakter

void configureButton() {
  pcf8574.begin();

  // Set button pin as INPUT and enable internal pull-up resistor
  pcf8574.write(BUTTON_PIN, HIGH);  // Enable internal pull-up

  attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), buttonISR, FALLING);
}

void sendUidToServer(String uid) {
  HTTPClient http;
  String serverUrl = "http://" + String(flaskServerIp) + ":5000/update_uid";
  String postData = "uid=" + uid;

  http.begin(wifiClient, serverUrl);
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  int httpCode = http.POST(postData);

  Serial.println(uid);
  Serial.println(httpCode);

  http.end();
}

void setup() {
  Serial.begin(9600);
  configureButton();
  WiFi.begin(ssid, password);  // Mencoba terhubung ke WiFi

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println("Connected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  SPI.begin();
  mfrc522.PCD_Init();
  pinMode(LED_G, OUTPUT);
  pinMode(RELAY, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  digitalWrite(BUZZER, LOW);
  digitalWrite(RELAY, HIGH);

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Tap Your Card");

  Serial.println("Put your card to the reader...");
  Serial.println();
}

void loop() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Tap Your Card...");
  lcd.setCursor(0, 1);
  lcd.print("Status : Lock");

  int buttonState = pcf8574.read(BUTTON_PIN);

  if (buttonPressed || buttonState == LOW) {
    Serial.println("Button Pressed!");
    lcd.clear();
    lcd.print("Access Granted");
    digitalWrite(RELAY, HIGH);
    digitalWrite(BUZZER, HIGH);
    delay(250);
    digitalWrite(BUZZER, LOW);
    digitalWrite(LED_G, HIGH);

    delay(ACCESS_DELAY);

    digitalWrite(RELAY, LOW);
    digitalWrite(LED_G, LOW);

    lcd.clear();
    lcd.print("Card Reader");
    lcd.setCursor(0, 1);
    lcd.print("Ready...");

    buttonPressed = false;
  }

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();

  if (!mfrc522.PICC_IsNewCardPresent()) {
    digitalWrite(RELAY, HIGH);
    digitalWrite(LED_G, LOW);
    digitalWrite(BUZZER, LOW);  // Tidak ada bunyi ketika tidak ada kartu yang terdeteksi
    delay(500);  // Delay untuk menghindari berkedip saat terus-menerus memeriksa kartu
    return;
  }

  if (!mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  String content = "";

  for (byte i = 0; i < mfrc522.uid.size; i++) {
    content.concat(String(mfrc522.uid.uidByte[i] < 0x10 ? "0" : ""));
    content.concat(String(mfrc522.uid.uidByte[i], HEX));
  }
  content.toUpperCase();

  String sanitizedContent = content;

  bool isAuthorized = false;

  for (int i = 0; i < sizeof(authorizedCards) / sizeof(authorizedCards[0]); i++) {
    if (sanitizedContent == authorizedCards[i].uid) {
      isAuthorized = true;
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print(authorizedCards[i].name);
      lcd.setCursor(0, 1);
      lcd.print("Status : Open");
      digitalWrite(RELAY, LOW);
      digitalWrite(BUZZER, HIGH);
      delay(250);
      digitalWrite(BUZZER, LOW);
      digitalWrite(LED_G, HIGH);

      sendUidToServer(sanitizedContent);

      delay(ACCESS_DELAY);

      digitalWrite(RELAY, HIGH);
      digitalWrite(LED_G, LOW);
      lcd.clear();
      break;
    }
  }

  if (!isAuthorized) {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Access Denied");
    lcd.setCursor(0, 1);
    lcd.print("Registering ID...");

    sendUidToServer(sanitizedContent);

    for (int j = 0; j < 2; j++) {
      digitalWrite(BUZZER, HIGH);
      delay(500);
      digitalWrite(BUZZER, LOW);
      delay(100);
    }

    delay(DENIED_DELAY);
    digitalWrite(BUZZER, LOW);
  }

  // Reset RFID setelah selesai membaca kartu
  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
}

