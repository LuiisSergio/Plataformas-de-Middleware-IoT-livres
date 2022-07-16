#define WIFI_SSID "" // Nome da rede WIFI
#define WIFI_PASS "" // Senha da rede wifi
static bool hasWifi   = false;

void conectaWifi(){
  Serial.println(" > Wifi");
  Serial.println("Starting connecting WiFi");
  delay(10);
  WiFi.mode(WIFI_AP);
  WiFi.begin(WIFI_SSID,WIFI_PASS);
  while(WiFi.status() != WL_CONNECTED){
    delay(500);
    Serial.print(".");
    hasWifi = false;
  }
  hasWifi = true;
  Serial.println("WiFi connected");
  Serial.print("Ip address: ");
  Serial.println(WiFi.localIP());
}
