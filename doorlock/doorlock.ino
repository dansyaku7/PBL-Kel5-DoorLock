#include <ESP8266WiFi.h>
#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN D4
#define RST_PIN D3
#define LED_G D1
#define LED_R D2
#define RELAY D0
#define BUZZER D8
#define ACCESS_DELAY 2000
#define DENIED_DELAY 1000

MFRC522 mfrc522(SS_PIN, RST_PIN);

struct AuthorizedCard {
  String uid;
  String name;
};

AuthorizedCard authorizedCards[3] = {
  {"5B 4D 48 21", "Kelompok 5"},
  {"05 8A 75 35 6D C1 00", "Irfan"},
  {"AD DE ED A5", "New User"}  // UID dan nama baru
};

void setup() {
  Serial.begin(9600);
  SPI.begin();
  mfrc522.PCD_Init();
  pinMode(LED_G, OUTPUT);
  pinMode(LED_R, OUTPUT);
  pinMode(RELAY, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  digitalWrite(BUZZER, LOW);
  digitalWrite(RELAY, HIGH);
  Serial.println("Put your card to the reader...");
  Serial.println();
}

void loop() {
  if (!mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  if (!mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  Serial.print("UID tag :");
  String content = "";

  for (byte i = 0; i < mfrc522.uid.size; i++) {
    Serial.print(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " ");
    Serial.print(mfrc522.uid.uidByte[i], HEX);
    content.concat(String(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " "));
    content.concat(String(mfrc522.uid.uidByte[i], HEX));
  }

  Serial.println();
  Serial.print("User : ");
  content.toUpperCase();

  // Periksa apakah UID terdapat dalam array kartu yang diotorisasi
  bool isAuthorized = false;
  for (int i = 0; i < sizeof(authorizedCards) / sizeof(authorizedCards[0]); i++) {
    if (content.substring(1) == authorizedCards[i].uid) {
      isAuthorized = true;
      Serial.println("Authorized access for " + authorizedCards[i].name);
      Serial.println();
      delay(200);
      digitalWrite(RELAY, LOW);
      digitalWrite(BUZZER, HIGH);
      delay(250); // Buzzer menyala selama 1 detik
      digitalWrite(BUZZER, LOW);
      digitalWrite(LED_G, HIGH);
      delay(ACCESS_DELAY);
      digitalWrite(RELAY, HIGH);
      digitalWrite(LED_G, LOW);
      break;  // Keluar dari loop jika akses diotorisasi
    }
  }

  // Jika UID tidak terdapat dalam array yang diotorisasi
  if (!isAuthorized) {
    Serial.println("Access denied");
    digitalWrite(LED_R, HIGH);
    for (int i = 0; i < 2; i++) {
      digitalWrite(BUZZER, HIGH);
      delay(500); // Buzzer menyala selama 100 milidetik
      digitalWrite(BUZZER, LOW);
      delay(100); // Delay antara bunyi buzzer
    }
    delay(DENIED_DELAY);
    digitalWrite(BUZZER, LOW);
    digitalWrite(LED_R, LOW);
  }
}
