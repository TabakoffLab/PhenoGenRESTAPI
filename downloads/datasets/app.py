import os, json, pymysql, boto3, logging
import MyDBConnection

logger = logging.getLogger()
logger.setLevel(logging.INFO)

selectDataset="select * from rna_dataset2"

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

def formatResponse(message,datasets):
    results={}
    results = {
        "message": message,
        "parameters": {
            "ResultCount": len(datasets)
        },
        "data": datasets}
    return results

def getDatasets(conn,payload):
    ds=[]
    cursor=conn.cursor()
    query=selectDataset
    genomeVer=""
    organism=""
    panel=""
    type=""
    tissue=""
    if (payload != None and payload != ""):
        first = True
        if ('genomeVer' in payload):
            query = query + " where genomever='" + payload['genomeVer'] + "'"
            first=False
        if('organism' in payload):
            if(first):
                query=query+" where "
                first=False
            else:
                query=query+" and "
            query=query+" organism='"+payload['organism']+"'"
        if('panel' in payload):
            if (first):
                query = query + " where "
                first = False
            else:
                query = query + " and "
            query=query+" strain_panel='"+payload['panel']+"'"
        if('type' in payload):
            type=""
            if(payload['type']=="totalRNA"):
                type="ribosome depleted totalRNA"
            elif(payload['type']=="smallRNA"):
                type="smallRNA"
            if (first):
                query = query + " where "
                first = False
            else:
                query = query + " and "
            query=query+" seq_type='"+type+"'"
        if('tissue' in payload):
            if (first):
                query = query + " where "
                first = False
            else:
                query = query + " and "
            query=query+" tissue='"+payload['tissue']+"'"
            
    cursor.execute(query)
    res = cursor.fetchmany()
    while (len(res)):
        for r in res:
            tmp={}
            tmp['ID']=r[0]
            tmp['Organism']=r[1]
            tmp['Panel']=r[3]
            tmp['Description']=r[4]
            tmp['Created']=str(r[6])
            tmp['Tissue']=r[8]
            tmp['SeqType']=r[9]
            tmp['GenomeVer']=r[10]
            ds.append(tmp)
        res = cursor.fetchmany()
    cursor.close()
    return ds

def lambda_handler(event, context):
    operation = 'GET'
    if ('httpMethod' in event):
        operation = event['httpMethod']
    message = ""
    
    if operation == 'GET':
        payload = None
        if ('querystring' in event['params']):
            payload = event['params']['querystring']
        
        conn = MyDBConnection.ConnectDB()
        datasets=getDatasets(conn,payload)
        conn.close()
        results=formatResponse(message,datasets)
        return respond(None, results)
    else:
        return respond(None)


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