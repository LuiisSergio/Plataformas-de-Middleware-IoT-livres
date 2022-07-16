#include <HTTPClient.h>

#define FUNCTION_URL  "https://<aplicacao_de_funcao_name>.azurewebsites.net/api/<funcao_name>" // para obter acesse aplicativos de função, escolha sua função e em seguida "Obter URL da Função"
#define FUNCTION_KEY  "" // Para obter vá em chaves da aplicação em seguida crie ou escolha uma
#define DEVICE "esp32"
int httpLock = 0;


void httpPost(void * parameters){
  if(WiFi.status() == WL_CONNECTED){
    httpLock = 1;
    HTTPClient http;
    http.begin(FUNCTION_URL);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("x-functions-key", FUNCTION_KEY);
    String *param  = (String*)parameters;
    String value  = param[1];
    String sensor = param[0];
    
    int on = digitalRead(PIN);
    String state = on ? "true" : "false";
    String json = "{\"id\": \""+String(DEVICE)+"\",\"name\": \""+String(sensor)+"\",\"value\": \""+String(value)+"\", \"state\": \""+state+"\"}";
    Serial.println("payload: "+json);
    http.setTimeout(5000);
    http.setConnectTimeout(20000);
    int httpResponseCode = http.POST(json);
    //Serial.println(httpResponseCode);
    if(httpResponseCode > 0){
      String response = http.getString();
      Serial.println(response);  
    }else{
      Serial.print("Error on sending post: ");  
      Serial.println(httpResponseCode);  
    }
    
    http.end();
  }
  httpLock = 0;
  vTaskDelete(NULL);
}
