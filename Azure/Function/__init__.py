import logging
import json
import azure.functions as func
import requests
from opencensus.extension.azure.functions import OpenCensusExtension
from opencensus.trace import config_integration
import time
import urllib
import hmac
import hashlib
import base64
import six.moves.urllib as urllib
from azure.cosmos import exceptions, CosmosClient, PartitionKey, cosmos_client
import os

config_integration.trace_integrations(['requests'])

settings_db = {
    'host': os.environ.get('ACCOUNT_HOST', 'https://<nome>.documents.azure.com:443/'), # insira o nome do cosmosDB
    'master_key': os.environ.get('ACCOUNT_KEY', ''), # insira a chave do banco
    'database_id': os.environ.get('COSMOS_DATABASE', ''), # insira o nome do db
    'container_id': os.environ.get('COSMOS_CONTAINER', 'itens'), # insira o nome da tabela
}

settings_IoT = {
    'hub_URI': "<nome>.azure-devices.net", # insira o nome do hubiot
    'hub_URL': 'https://<nome>.azure-devices.net/twins/<devicename>/methods?api-version=2018-06-30', # insira o nome do hub e o device name
    'hub_key': '' # insira a chave do hub
}

HOST         = settings_db['host']
MASTER_KEY   = settings_db['master_key']
DATABASE_ID  = settings_db['database_id']
CONTAINER_ID = settings_db['container_id']

HUB_DEV_URI = settings_IoT['hub_URI']
HUB_DEV_URL = settings_IoT['hub_URL']
HUB_KEY     = settings_IoT['hub_key']


def list_databases(client):
    print('Databases:')

    databases = list(client.list_databases())

    if not databases:
        return

    for database in databases:
        print(database['id'])
def read_database(client, id):
    try:
        database = client.get_database_client(id)
        print('Database with id \'{0}\' was found, it\'s link is {1}'.format(id, database.database_link))

    except exceptions.CosmosResourceNotFoundError:
        print('A database with id \'{0}\' does not exist'.format(id))
def find_database(client, id):
    databases = list(client.query_databases({
        "query": "SELECT * FROM r WHERE r.id=@id",
        "parameters": [
            { "name":"@id", "value": id }
        ]
    }))

    if len(databases) > 0:
        print('Database with id \'{0}\' was found'.format(id))
    else:
        print('No database with id \'{0}\' was found'. format(id))
def find_container(db, id):
    containers = list(db.query_containers(
        {
            "query": "SELECT * FROM r WHERE r.id=@id",
            "parameters": [
                { "name":"@id", "value": id }
            ]
        }
    ))

    if len(containers) > 0:
        print('Container with id \'{0}\' was found'.format(id))
    else:
        print('No container with id \'{0}\' was found'. format(id))
def read_items(container):
    # NOTE: Use MaxItemCount on Options to control how many items come back per trip to the server
    #       Important to handle throttles whenever you are doing operations such as this that might
    #       result in a 429 (throttled reuest)
    item_list = list(container.read_all_items(max_item_count=10))

    print('Found {0} items'.format(item_list.__len__()))

    for doc in item_list:
        print('Item Id: {0}'.format(doc.get('id')))
def registryExist(container, doc_id, sensor):
    # enable_cross_partition_query should be set to True as the container is partitioned
    items = list(container.query_items(
        query="SELECT * FROM r WHERE r.id=@id AND r.category=@sensor",
        parameters=[
            { "name":"@id", "value": doc_id },
            { "name":"@sensor", "value": sensor}
        ],
        enable_cross_partition_query=True
    ))
    try:
        items[0].get("id")
        return items[0];
    except:
        return False;
    
def create_items(container, data):
    # Create a SalesOrder object. This object has nested properties and various types including numbers, DateTimes and strings.
    # This can be saved as JSON as is without converting into rows/columns.
    container.create_item(body=data)
def upsert_item(container, doc_id, data, sensor):
    if registryExist(container, doc_id, sensor):
        read_item = container.read_item(item=doc_id, partition_key=sensor)
        read_item['value'].update(data['value']);
        container.upsert_item(body=read_item)
    else:
        create_items(container, data)
    
  
   
#OpenCensusExtension.configure()
def main(req: func.HttpRequest) -> func.HttpResponse:

    #try:
    logging.info('Python HTTP trigger function processed a request.')
    
    
    id          = req.params.get('id') # device name
    state       = req.params.get('state') 
    sensorName  = req.params.get('name') # valor medido pelo sensor
    sensorValue = req.params.get('value') # valor medido pelo sensor

    if not id:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            id          = req_body.get('id')
            state       = req_body.get('state')
            sensorName  = req_body.get('name') # valor medido pelo sensor
            sensorValue = req_body.get('value');

    client = cosmos_client.CosmosClient(HOST, {'masterKey': MASTER_KEY} )
    sasToken = SasToken(HUB_DEV_URI, HUB_KEY,"iothubowner");
    if id and sensorValue and sensorValue and state: #salvar o valor no banco
        db        = client.create_database_if_not_exists(id=DATABASE_ID)
        container = db.create_container_if_not_exists(id=CONTAINER_ID, partition_key=PartitionKey(path='/id', kind='Hash'))
        data      = {
                    'id'    : id,
                    'category': sensorName,
                    'value' : { time.time() : sensorValue }
                }
        upsert_item(container, id, data, sensorName)
        newState = state;
        if state == "true" and int(sensorValue) < 1000: # reservatorio atingiu a capacidade maxima e deve desligar a bomba
            newState = "false";
        elif state == "false" and int(sensorValue) > 1000: # reservatorio atingiu a capacidade minima e deve desligar a bomba
            newState = "true";
        if newState != state:
            raw={
                "methodName": "change-state",
                "responseTimeoutInSeconds": "200",
                "payload": {
                    "state": newState
                }
            }   
            headers = {
                'Authorization': str(sasToken)                          
            }
            requests.post(HUB_DEV_URL, data=json.dumps(raw), headers=headers)
        
        return func.HttpResponse(
            "Sensor Value receved",
            status_code=200 
        )                
    else:
        return func.HttpResponse(
            "This HTTP triggered function executed successfully but parameters are missing",
            status_code=200 
        )





class SasTokenError(Exception):
    """Error in SasToken"""

    def __init__(self, message, cause=None):
        """Initializer for SasTokenError
        :param str message: Error message
        :param cause: Exception that caused this error (optional)
        """
        super(SasTokenError, self).__init__(message)
        self.cause = cause
class SasToken(object):
    """Shared Access Signature Token used to authenticate a request
    Parameters:
    uri (str): URI of the resouce to be accessed
    key_name (str): Shared Access Key Name
    key (str): Shared Access Key (base64 encoded)
    ttl (int)[default 3600]: Time to live for the token, in seconds
    Data Attributes:
    expiry_time (int): Time that token will expire (in UTC, since epoch)
    ttl (int): Time to live for the token, in seconds
    Raises:
    SasTokenError if trying to build a SasToken from invalid values
    """

    _encoding_type = "utf-8"
    _service_token_format = "SharedAccessSignature sr={}&sig={}&se={}&skn={}"
    _device_token_format = "SharedAccessSignature sr={}&sig={}&se={}"

    def __init__(self, uri, key, key_name=None, ttl=3600):
        self._uri = urllib.parse.quote_plus(uri)
        self._key = key
        self._key_name = key_name
        self.ttl = ttl
        self.refresh()

    def __str__(self):
        return self._token

    def refresh(self):
        """
        Refresh the SasToken lifespan, giving it a new expiry time
        """
        self.expiry_time = int(time.time() + self.ttl)
        self._token = self._build_token()

    def _build_token(self):
        """Buid SasToken representation
        Returns:
        String representation of the token
        """
        try:
            message = (self._uri + "\n" + str(self.expiry_time)).encode(self._encoding_type)
            signing_key = base64.b64decode(self._key.encode(self._encoding_type))
            signed_hmac = hmac.HMAC(signing_key, message, hashlib.sha256)
            signature = urllib.parse.quote(base64.b64encode(signed_hmac.digest()))
        except (TypeError, base64.binascii.Error) as e:
            raise SasTokenError("Unable to build SasToken from given values", e)
        if self._key_name:
            token = self._service_token_format.format(
                self._uri, signature, str(self.expiry_time), self._key_name
            )
        else:
            token = self._device_token_format.format(self._uri, signature, str(self.expiry_time))
        return token