#include <SPI.h>
#include <MFRC522.h>
#define BLYNK_PRINT Serial
#include <ESP8266WiFi.h>
#include <BlynkSimpleEsp8266.h>

class RFIDUser {
public:
  RFIDUser(byte uidByte0, byte uidByte1, byte uidByte2, byte uidByte3, const char *name)
    : uidByte0(uidByte0), uidByte1(uidByte1), uidByte2(uidByte2), uidByte3(uidByte3), name(name) {}

  byte getUidByte0() const { return uidByte0; }
  byte getUidByte1() const { return uidByte1; }
  byte getUidByte2() const { return uidByte2; }
  byte getUidByte3() const { return uidByte3; }
  const char *getName() const { return name; }

private:
  byte uidByte0;
  byte uidByte1;
  byte uidByte2;
  byte uidByte3;
  const char *name;
};

RFIDUser users[] = {
  RFIDUser(11, 22, 33, 44, "User01"),
  RFIDUser(11, 12, 13, 14, "User02"),
  RFIDUser(21, 22, 23, 24, "User03"),
};

class RFIDDoorLock {
public:
  RFIDDoorLock(byte ssPin, byte rstPin, byte lockPin)
    : mfrc522(rstPin, ssPin), lockPin(lockPin) {}

  void setup() {
    Serial.begin(9600);
    Blynk.begin(auth, ssid, pass);
    pinMode(lockPin, OUTPUT);
    digitalWrite(lockPin, LOW);
    SPI.begin();
    mfrc522.PCD_Init();
    timer.setInterval(1000L, std::bind(&RFIDDoorLock::iot_rfid, this));
  }

  void loop() {
    timer.run();
    Blynk.run();
  }

private:
  MFRC522 mfrc522;
  byte lockPin;
  SimpleTimer timer;
  
  void iot_rfid() {
    // ... (kode lainnya)

    for (const RFIDUser &user : users) {
      if (
        (mfrc522.uid.uidByte[0] == user.getUidByte0()) &&
        (mfrc522.uid.uidByte[1] == user.getUidByte1()) &&
        (mfrc522.uid.uidByte[2] == user.getUidByte2()) &&
        (mfrc522.uid.uidByte[3] == user.getUidByte3())
      ) {
        Serial.println(user.getName());
        Blynk.virtualWrite(V2, user.getName());
        digitalWrite(lockPin, HIGH);
        delay(3000);
        digitalWrite(lockPin, LOW);
        return; // Keluar dari loop setelah menemukan kartu yang cocok
      }
    }

    Serial.println("Unregistered User");
  }
};

// Inisialisasi objek RFIDDoorLock
RFIDDoorLock doorLock(2, 0, D0);

// BLYNK_WRITE dan lain-lain

void setup() {
  doorLock.setup();
}

void loop() {
  doorLock.loop();
}
