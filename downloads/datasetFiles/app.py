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
    response['parameters'] = {}
    return response


def formatResponse(message, result,resultFiles):
    results = {}
    if result is not None:
        results = {
            "message": message,
            "parameters": {
            
            },
            "dataset": {
                'ID': result['ID'],
                'Organism': dataset['Organism'],
                'Panel': dataset['Panel'],
                'Description': dataset['Description'],
                'Created': dataset['Created'],
                'Tissue': dataset['Tissue'],
                'SeqType': dataset['SeqType'],
                'GenomeVer': dataset['GenomeVer'],
                'metaData': meta,
                'results': result
            }
        }
        if resultFiles is not None:
            results['resultFiles'] = resultFiles
    else:
        results = {
            "message": message,
            "parameters": {},
            "datasetResult": {}
        }
    return results


def getDatasetResult(conn, payload):
    ds = {}
    cursor = conn.cursor()
    query = selectDataset + str(payload['datasetID'])
    logger.info(query)
    cursor.execute(query)
    res = cursor.fetchone()
    if res is not None:
        ds['ID'] = res[0]
        ds['Organism'] = res[1]
        ds['Panel'] = res[3]
        ds['Description'] = res[4]
        ds['Created'] = str(res[6])
        ds['Tissue'] = res[8]
        ds['SeqType'] = res[9]
        ds['GenomeVer'] = res[10]
    cursor.close()
    return ds


def getResultFiles(conn, payload):
    results = []
    cursor = conn.cursor()
    query = selectResults + str(payload['datasetID'])
    logger.info(query)
    cursor.execute(query)
    res = cursor.fetchall()
    for r in res:
        tmp = {}
        tmp['ID'] = r[0]
        tmp['type'] = r[2]
        tmp['genomeVersion'] = r[3]
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
        result = None
        resultFiles = None
        dsrID = -1
        conn = None
        if ('querystring' in event['params']):
            payload = event['params']['querystring']
        if ("resultID" in payload and int(payload['resultID']) > 0):
            dsrID = payload['resultID']
            conn = MyDBConnection.ConnectDB()
            result = getDatasetResult(conn, payload)
        else:
            return getResponse(None,getHelp())
        if (result is None):
            message = "Dataset Result (id:" + str(dsrID) + ") not found."
            return (message, {})
        else:
            resultFiles = getResultFiles(conn, payload)
        if conn is not None:
            conn.close()
        if dataset is not None:
            response = formatResponse(message, result,resultFiles)
            return respond(None, response)
        else:
            return respond(None, {})
        return respond(InputError('Parameters', 'required parameters missing'))
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