#include "secrets.h"
#include <WiFiClientSecure.h>
#include <MQTTClient.h>
#include <ArduinoJson.h>
#include "WiFi.h"
#include <Ultrasonic.h> 

// The MQTT topics that this device should publish/subscribe
#define AWS_IOT_PUBLISH_TOPIC   "esp32/pub" // topico de escrita
#define AWS_IOT_SUBSCRIBE_TOPIC "esp32/sub" // topico de leitura

// pinos do sensor HC-SR04
#define pino_trigger 26 // pino para trigger
#define pino_echo 33 // pino para echo

// Led simbolizando a bomba
#define led 27


Ultrasonic ultrasonic(pino_trigger, pino_echo);
WiFiClientSecure net = WiFiClientSecure();
MQTTClient client = MQTTClient(256);
DynamicJsonDocument doc(1024);
float cmMsec, inMsec;

void publishMessage(){
  StaticJsonDocument<200> doc;
  doc["time"]   = millis();
  doc["id"]     = "esp32";
  doc["name"]   = "proximidade";
  doc["value"]  = cmMsec;
  doc["state"]  = digitalRead(led) == 1? "true" : "false";
  char jsonBuffer[512];
  serializeJson(doc, jsonBuffer); // 
  
  Serial.print("Publishing :");
  Serial.print(AWS_IOT_PUBLISH_TOPIC);
  Serial.print(" Distancia em cm: ");
  Serial.println(cmMsec);
  client.publish(AWS_IOT_PUBLISH_TOPIC, jsonBuffer);
}

void messageHandler(String &topic, String &payload) {
  Serial.println("Incoming: " + topic + " - " + payload);  
  deserializeJson(doc, payload);

  StaticJsonDocument<200> doc;
  deserializeJson(doc, payload);
  const char* message = doc["led"];
  digitalWrite(led, strcmp(message,"true") == 0 ? HIGH : LOW);
}
void lerSensor(){
  // Serial.println("Lendo dados do sensor...");
  //Le as informacoes do sensor, em cm e pol
  
  long microsec = ultrasonic.timing();
  cmMsec = ultrasonic.convert(microsec, Ultrasonic::CM);
  inMsec = ultrasonic.convert(microsec, Ultrasonic::IN);
  //Exibe informacoes no serial monitor
  Serial.print("Distancia em cm: ");
  Serial.println(cmMsec);
  //Serial.print(" - Distancia em polegadas: ");
  //Serial.println(inMsec);
  publishMessage();     
   
}
void setup() {
  Serial.begin(115200);
  connectAWS();
  pinMode(led, OUTPUT);
}

void loop() {
  client.loop();
  lerSensor();
  delay(2000);
}

void connectAWS()
{
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to Wi-Fi");

  while (WiFi.status() != WL_CONNECTED){
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  // Configure WiFiClientSecure to use the AWS IoT device credentials
  net.setCACert(AWS_CERT_CA);
  net.setCertificate(AWS_CERT_CRT);
  net.setPrivateKey(AWS_CERT_PRIVATE);

  // Connect to the MQTT broker on the AWS endpoint we defined earlier
  client.begin(AWS_IOT_ENDPOINT, 8883, net);

  // Create a message handler
  client.onMessage(messageHandler);

  Serial.print("Connecting to AWS IOT");

  while (!client.connect(THINGNAME)) {
    delay(100);
  }

  if(!client.connected()){
    Serial.println("AWS IoT Timeout!");
    return;
  }
  // Subscribe to a topic
  client.subscribe(AWS_IOT_SUBSCRIBE_TOPIC);
  Serial.println("");
  Serial.println("AWS IoT Connected!");
}
