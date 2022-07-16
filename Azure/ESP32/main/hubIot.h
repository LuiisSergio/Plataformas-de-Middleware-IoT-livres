#define connectionString "HostName=<hubIoTName>.azure-devices.net;DeviceId=<deviceId>;SharedAccessKey=<AuthKey>"
#define PIN 19

static bool hasIoTHub = false;
static int device_method_callback(const char *methodName, const unsigned char *payload, int size, unsigned char **response, int *response_size){
  LogInfo("Metodo invodado: %s", methodName);
  char *responseMessage = "\"Sucess\"";
  int result = 200;

  if(strcmp(methodName, "change-state") == 0){
    
    StaticJsonDocument<64> jsonBuffer;
    DeserializationError error = deserializeJson(jsonBuffer, payload, size);
    const JsonObject &data = jsonBuffer.template as<JsonObject>();
    String state = data["state"];
    LogInfo("Mudança de estado: %s", state);
    //LogInfo("%s", state);
    
    if(state == "null"){
      LogInfo("Sem estado");
      responseMessage = "\"erro no estado\"";
      result = 400;
    }
    int on = state == "true";
    //LogInfo("%d", on);
    digitalWrite(PIN, on);
    if (on){
      responseMessage = "{\"currentState\":\"false\"}";
    }else{
      responseMessage = "{\"currentState\":\"true\"}";
    }
  }else if (strcmp(methodName, "get-state") == 0){
    LogInfo("Get-state");
    int on = digitalRead(PIN);
    if (on){
      responseMessage = "{\"currentState\":\"false\"}";
    }else{
      responseMessage = "{\"currentState\":\"true\"}";
    }
  }else{
    LogInfo("Metodo %s nao econtrado", methodName);
    responseMessage = "\"Metodo nao encontrado\"";
    result=404;
  }

  *response_size = strlen(responseMessage);
  *response = (unsigned char*)strdup(responseMessage);
  return result;
}

void conectaIoTHub(){
  Serial.println(" > IoT Hub");
  
  if(!Esp32MQTTClient_Init((const uint8_t*)connectionString, true)){
    hasIoTHub = false;
    Serial.println("Initializing IoT hub failed");
  }
  hasIoTHub = true;
  Esp32MQTTClient_SetDeviceMethodCallback(device_method_callback);
}
