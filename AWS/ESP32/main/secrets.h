#include <pgmspace.h>

#define THINGNAME "" // nome do dispositivo cadastrado na AWS

const char* WIFI_SSID = ""; // nome da rede wifi
const char* WIFI_PASSWORD =  ""; // senha da rede wifi

const char AWS_IOT_ENDPOINT[] = ""; // endpoint
// para descobrir o seu endpoint acesse o console da AWS e execute o comando:
// $ aws iot describe-endpoint --endpoint-type iot:Data-ATS


// Amazon Root CA 1
static const char AWS_CERT_CA[] PROGMEM = R"EOF(
-----BEGIN CERTIFICATE-----
  <Escreva o certificado aqui>
-----END CERTIFICATE-----
)EOF";

// Device Certificate
static const char AWS_CERT_CRT[] PROGMEM = R"KEY(
-----BEGIN CERTIFICATE-----
  <Escreva o certificado aqui>
-----END CERTIFICATE-----
)KEY";

// Device Private Key
static const char AWS_CERT_PRIVATE[] PROGMEM = R"KEY(
-----BEGIN RSA PRIVATE KEY-----
  <Escreva o certificado aqui>
-----END RSA PRIVATE KEY-----
)KEY";
