import os, json, pymysql, boto3, logging
import MyDBConnection

logger = logging.getLogger()
logger.setLevel(logging.INFO)

selectResults = "SELECT * FROM rna_dataset_results where rna_dataset_result_id="
selectResultFiles = "SELECT * FROM rna_dataset_results_files where rna_dataset_result_id="


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
    response['parameters']['resultID'] = {
        "description": "resultID parameter - Required - ID of the dataset to retreive."}
    return response


def formatResponse(message, result,resultFiles):
    results = {}
    if result is not None:
        results = {
            "message": message,
            "parameters": {
            
            },
            "datasetResult": result
        }
        if resultFiles is not None:
            results['datasetResult']['resultFiles'] = resultFiles
    else:
        results = {
            "message": message,
            "parameters": {},
            "datasetResult": {}
        }
    return results


def getDatasetResult(conn, payload):
    ds = None
    cursor = conn.cursor()
    query = selectResults + str(payload['resultID'])
    if('datasetID' in payload):
        query=query+" and rna_dataset_id ="+str(payload['datasetID'])
    logger.info(query)
    cursor.execute(query)
    res = cursor.fetchone()
    if res is not None:
        ds={}
        ds['ID'] = res[0]
        ds['type'] = res[2]
        ds['genomeVersion'] = res[3]
        ds['version'] = res[4]
        ds['createdDate'] = str(res[5])
    cursor.close()
    return ds


def getResultFiles(conn, payload):
    results = None
    cursor = conn.cursor()
    query = selectResultFiles + str(payload['resultID'])
    logger.info(query)
    cursor.execute(query)
    res = cursor.fetchall()
    if(len(res)>1):
        results=[]
    for r in res:
        tmp = {}
        tmp['fileID'] = r[0]
        tmp['uploadDate'] = str(r[2])
        tmp['fileName'] = r[3]
        tmp['URL'] = "https://phenogen.org"+r[5]+r[4]
        tmp['checksum'] = r[6]
        tmp['genomeVersion'] = r[8]
        tmp['description'] = r[9]
        tmp['annotation'] = r[10]
        tmp['level'] = r[11]
        strainMeans=False
        if(r[12]==1):
            strainMeans=True
        tmp['strainMeans'] = strainMeans
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
        result = None
        resultFiles = None
        dsrID = -1
        dsID = -1
        conn = None
        if ('querystring' in event['params']):
            payload = event['params']['querystring']
        if ("resultID" in payload and int(payload['resultID']) > 0):
            if("datasetID" in payload and int(payload['datasetID']) > 0):
                dsID= payload['datasetID']
                dsrID = payload['resultID']
                conn = MyDBConnection.ConnectDB()
                result = getDatasetResult(conn, payload)
            else:
                return respond(None, getHelp())
        else:
            return respond(None,getHelp())
        if (result is None):
            message = "Dataset(id:"+str(dsID)+") and Result (id:" + str(dsrID) + ") not found. Please double check that you have provided the correct IDs."
            return respond(InputError('Parameters',message), getHelp())
        else:
            resultFiles = getResultFiles(conn, payload)
        if conn is not None:
            conn.close()
        if result is not None:
            response = formatResponse(message, result,resultFiles)
            return respond(None, response)
        else:
            return respond(None, {})
        return respond(InputError('Parameters', 'required parameters missing'),getHelp())
    else:
        return respond(InputError('HTTPMethod', 'Unsupported method'))


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