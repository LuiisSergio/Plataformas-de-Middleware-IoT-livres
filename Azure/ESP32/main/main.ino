#include <ArduinoJson.h>
#include <WiFi.h>
#include "Esp32MQTTClient.h"
#include <HTTPClient.h>

//custom include
#include "conectaWifi.h"
#include "hubIot.h"
#include "httpPost.h"


#define potenciometro 36
int value = 0;
String mensage[2];

void setup(){
  Serial.begin(115200);
  Serial.println("ESP32 Device");
  Serial.println("initializaing...");
  conectaWifi();
  conectaIoTHub();
  pinMode(PIN, OUTPUT);
}
void loop(){
  Esp32MQTTClient_Check();
  int valueNew = analogRead(potenciometro);
  
  if ((valueNew > value + 500 || valueNew < value - 500) && httpLock == 0){
    Serial.print("Enviando valor : ");
    Serial.println(valueNew);
    value = valueNew;
    mensage[0] = "potenciometro";
    mensage[1] = String(value);
    xTaskCreate(httpPost, "httpPost", 10000, &mensage, 1, NULL);  
    //delay(1500);         
  }
}
