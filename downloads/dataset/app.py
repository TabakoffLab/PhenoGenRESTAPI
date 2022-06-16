import os, json, pymysql, boto3, logging
import MyDBConnection

logger = logging.getLogger()
logger.setLevel(logging.INFO)

selectDataset="SELECT * FROM rna_dataset2 where rna_dataset_id="
selectResults="SELECT * FROM rna_dataset_results where rna_dataset_id="
selectMeta="SELECT * FROM rna_dataset_results where rna_dataset_id="

def respond(err, res=None):
    body=""
    if err :
        if(res is not None):
            body={"message":err.message,"help": json.dumps(res)}
        else:
            body = {"message": err.message }
    else:
        body=json.dumps(res)
    return {
        'statusCode': '400' if err else '200',
        'body': body,
        'headers': {
            'Content-Type': 'application/json',
        },
        'isBase64Encoded': False
    }


def getHelp():
    response = {}
    response['methods'] = "GET"
    response['parameters'] = {}
    response['parameters']['datasetID'] = {
        "description": "datasetID parameter - Required - ID of the dataset to retreive."}
    return response

def formatResponse(message,dataset,meta,result):
    results={}
    if dataset is not None:
        results = {
            "message": message,
            "parameters": {
            
            },
            "dataset":{
                'ID':dataset['ID'],
                'Organism':dataset['Organism'],
                'Panel': dataset['Panel'],
                'Description': dataset['Description'],
                'Created': dataset['Created'],
                'Tissue': dataset['Tissue'],
                'SeqType': dataset['SeqType'],
                'GenomeVer':dataset['GenomeVer']
            }
        }
        if meta is not None:
            results['metaData']=meta
        if result is not None:
            results['results']=result
    else:
        results = {
            "message": message,
            "parameters": {},
            "dataset":{}
        }
    return results

def getDataset(conn,payload):
    ds={}
    cursor=conn.cursor()
    query=selectDataset+str(payload['datasetID'])
    logger.info(query)
    cursor.execute(query)
    res = cursor.fetchone()
    if res is not None:
        ds['ID']=res[0]
        ds['Organism']=res[1]
        ds['Panel']=res[3]
        ds['Description']=res[4]
        ds['Created']=str(res[6])
        ds['Tissue']=res[8]
        ds['SeqType']=res[9]
        ds['GenomeVer']=res[10]
    cursor.close()
    return ds

def getMetaData(conn,payload):
    meta={}
    #cursor = conn.cursor()
    #cursor.close()
    return meta


def getResultList(conn, payload):
    results=[]
    cursor = conn.cursor()
    query = selectResults + str(payload['datasetID'])
    logger.info(query)
    cursor.execute(query)
    res = cursor.fetchall()
    for r in res:
        tmp={}
        tmp['ID'] = r[0]
        tmp['type'] = r[2]
        tmp['genomeVersion']=r[3]
        tmp['version'] = r[4]
        tmp['createdDate'] = str(r[5])
        results.append(tmp)
    cursor.close()
    return results

def lambda_handler(event, context):
    operation = 'GET'
    if ('httpMethod' in event):
        operation = event['httpMethod']
    message = ""
    
    if operation == 'GET':
        payload = None
        dataset = None
        metaData = None
        results = None
        dsID=-1
        conn=None
        if ('querystring' in event['params']):
            payload = event['params']['querystring']
        if 'help' in payload:
            return respond(None,getHelp())
        else:
            if("datasetID" in payload and int(payload['datasetID'])>0):
                dsID=payload['datasetID']
                conn = MyDBConnection.ConnectDB()
                dataset = getDataset(conn, payload)
            else:
                message="missing required parameter:datasetID"
                return respond(InputError("MissingParameter",message),getHelp())
            if(dataset is None):
                message="Dataset (id:"+str(dsID)+") not found."
                return(message,{})
            else:
                metaData=getMetaData(conn,payload)
                results=getResultList(conn,payload)
            if conn is not None:
                conn.close()
            if dataset is not None:
                results=formatResponse(message,dataset,metaData,results)
                return respond(None, results)
            return respond(InputError('Error', 'An error has occurred'))
    else:
        return respond(InputError('HTTPMethod', 'Unsupported method'),getHelp())


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class InputError(Error):
    """Exception raised for errors in the input.

      Attributes:
          expression -- input expression in which the error occurred
          message -- explanation of the error
      """
    
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message