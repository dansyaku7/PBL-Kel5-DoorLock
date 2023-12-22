#include <ESP8266WiFi.h>
#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define SS_PIN D4
#define RST_PIN D3
#define LED_G D0
#define RELAY D0
#define BUZZER D8
#define ACCESS_DELAY 2000
#define DENIED_DELAY 1000

MFRC522 mfrc522(SS_PIN, RST_PIN);
LiquidCrystal_I2C lcd(0x27, 16, 2); // Sesuaikan alamat I2C dan ukuran LCD jika diperlukan

const char* ssid = "Queensa";      // Ganti dengan nama WiFi Anda
const char* password = "Mahira101010";  // Ganti dengan kata sandi WiFi Anda

struct AuthorizedCard {
  String uid;
  String name;
};

AuthorizedCard authorizedCards[3] = {
  {"5B 4D 48 21", "Kelompok 5 PBL"},
  {"05 8A 75 35 6D C1 00", "Irfan"},
  {"AD DE ED A5", "New User"}  // UID dan nama baru
};

void setup() {
  Serial.begin(9600);
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
    content.concat(String(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " "));
    content.concat(String(mfrc522.uid.uidByte[i], HEX));
  }
  content.toUpperCase();

  bool isAuthorized = false;
  String sanitizedContent = content.substring(1);  // Hapus karakter pertama (spasi)

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
      digitalWrite(BUZZER, LOW);  // Tidak ada bunyi setelah akses
      digitalWrite(LED_G, HIGH);

      delay(ACCESS_DELAY);

      digitalWrite(RELAY, HIGH);
      digitalWrite(LED_G, LOW);
      lcd.clear();
      break;  // Keluar dari loop jika akses diotorisasi
    }
  }

  if (!isAuthorized) {
    // Kartu tidak diotorisasi
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Access Denied");
    lcd.setCursor(0, 1);
    lcd.print("No Registered ID");
    for (int j = 0; j < 2; j++) {
      digitalWrite(BUZZER, HIGH);
      delay(500);
      digitalWrite(BUZZER, LOW);
      delay(100);
    }

    delay(DENIED_DELAY);
    digitalWrite(BUZZER, LOW);
  }
}
