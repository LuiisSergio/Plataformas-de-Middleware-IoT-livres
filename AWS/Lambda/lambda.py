import json
import boto3 # biblioteca responsavel por fazer a integração entre os serviços da AWS. Nesse caso o lambda com o DynamoDB
import array
import time

TOPICO 		= "esp32/sub";

#DB table infos
DB_TABLE 		= "";
PARTITION_KEY 	= "id";
SORT_KEY		= "sensor"


def lambda_handler(event, context):
	client = boto3.client('iot-data');
	data = json.dumps(event);
	data2 = json.loads(data);
	
	id = state = sensorName = sensorValue = None;
	
	if data2["id"]:
		id = data2["id"];
	if data2["state"]:
		state = data2["state"];
	if data2["name"]:
		sensorName = data2["name"];
	if data2["value"]:
		sensorValue = int(data2["value"]);
		
	if id and sensorValue and sensorValue and state: #salvar o valor no banco
		dynamodb=boto3.resource('dynamodb'); # aqui informamos o serviço que a bibilioteca vai acessar
		table = dynamodb.Table(DB_TABLE) # aqui informamos o nome da tabela criada
		upsert(id, sensorName, sensorValue, table) # função criada para analisar se o PARTITION_KEY/SORT_KEY ja existe e inserir o novo registro

		# analisamos a medição do sensor de proximidade e se:
		# o valor for menor que 15 a lambda deve setar o estado do led para deligado
		# o valor for maior que 15 a lambda deve setar o estado do led para ligado
		newState = state;
		if state == "true" and int(sensorValue) < 15: 
			newState = "false";
		elif state == "false" and int(sensorValue) > 15: 
			newState = "true";
    
    	# preparamos o json resposta para o esp32
		res = {	"led" : newState  }
	
		# publicando a mensagem no topico
		response = client.publish(
			topic = TOPICO,
			qos	  = 0,
			payload = json.dumps(res)
		)
		return "Sucess"
	else:
		return "Fail"
		
def upsert(id, name, value, db):
	ts		= int(float(time.time())); # pegando o timestamp atual
	try:
		data	= db.get_item(Key={PARTITION_KEY: id, SORT_KEY: name}); # buscando por registros do mesmo dispositivo e mesmo sensor
		values	= data['Item']['values']; # se o dado foi encontrado inserimos um novo registro
		values.update({str(ts): value })
		db.put_item(Item={PARTITION_KEY: id, SORT_KEY: name, 'values': values});
	except:
		db.put_item(Item={PARTITION_KEY: id, SORT_KEY: name, 'values': {str(ts): value }});	# se o dado nao foi encontrado criamos 
																					# um novo elemento e registramos a medição

