import os, json, pymysql, boto3, logging
import MyDBConnection

logger = logging.getLogger()
logger.setLevel(logging.INFO)

selectDataset="SELECT * FROM rna_dataset2 where rna_dataset_id="
selectResults="SELECT * FROM rna_dataset_results where rna_dataset_id="
selectMetaPipeline="SELECT * FROM rna_p2dr where rna_dataset_result_id in (select rna_dataset_result_id from rna_dataset_results where rna_dataset_id="
selectMetaPipeline2="SELECT * FROM rna_pipeline where rna_pipeline_id in ("
selectMetaPipeline3="SELECT * FROM rna_pipeline_steps where rna_pipeline_id in ("

selectMetaSample = "Select * from rna_ds_samples where rna_dataset_id="
selectMetaProtocol = "SELECT rp.RNA_PROTOCOL_ID,rp.title,rp.DESCRIPTION,rp.version,rpt.protocol_type,rp.filename,rp.PATH "+ \
    "FROM inia_prod.rna_protocols rp left outer join rna_protocol_type rpt on rpt.RNA_PROTOCOL_TYPE_ID=rp.RNA_PROTOCOL_TYPE_ID "+ \
    "where rna_protocol_id in (select RNA_PROTOCOL_ID from rna_ds_protocols where rna_sample_id in "+ \
    "(select rna_sample_id from rna_ds_samples where rna_dataset_id="



def respond(err, res=None):
    body=""
    if err :
        if(res is not None):
            body={"message":err.message,"help": json.dumps(res)}
        else:
            body = {"message": err.message }
    else:
        body=res #json.dumps(res)
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
        "description": "datasetID parameter - Required - ID of the dataset to retrieve."}
    return response

def formatResponse(message,dataset,meta,result):
    results={}
    if dataset is not None and 'datasetID' in dataset:
        results = {
            "message": message,
            "parameters": {
            
            },
            "dataset":{
                'ID':dataset['datasetID'],
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
        message="No Dataset Found: "+message
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
        ds['datasetID']=res[0]
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
    cursor = conn.cursor()
    query=selectMetaPipeline+str(payload['datasetID'])+")"
    print(query)
    cursor.execute(query)
    results=cursor.fetchall()
    pipelineIDs={}
    for r in results:
        if(not r[0] in pipelineIDs):
            pipelineIDs[r[0]]="1"
    plStr=""
    pipelines={}
    for id in pipelineIDs:
        plStr=plStr+","+str(id)
    if(len(plStr)>1):
        plStr = plStr[1:]
        query2=selectMetaPipeline2+plStr+")"
        cursor.execute(query2)
        results2=cursor.fetchall()
        for res in results2:
            pipeline={}
            pipeline['pipelineID']=res[0]
            pipeline['title']=res[1]
            pipeline['description']=res[2]
            pipeline['steps']=[]
            pipelines[str(res[0])]=pipeline
            
        query3 = selectMetaPipeline3 + plStr + ")"
        cursor.execute(query3)
        results3=cursor.fetchall()
        for res in results3:
            pipelineStep = {}
            pipelineStep['name'] = res[2]
            pipelineStep['stepType'] = res[3]
            pipelineStep['order'] = res[4]
            pipelineStep['scriptFile'] = res[5]
            pipelineStep['program'] = res[6]
            pipelineStep['programVersion'] = res[7]
            pipelineStep['commandLine'] = res[8]
            pipelineStep['startReadCount'] = res[9]
            pipelineStep['endReadCount'] = res[10]
            pipelineStep['programURL'] = res[12]
            pipelines[str(res[1])]['steps'].append(pipelineStep)
    pipelineList=[]
    for p in pipelines:
        pipelineList.append(pipelines[p])
    meta['pipelines'] = pipelineList
    sampleList=[]
    cursor.execute(selectMetaSample+str(payload['datasetID']))
    results4 = cursor.fetchall()
    for res in results4:
        sample={}
        sample['sampleName']=res[2]
        sample['strain'] = res[3]
        sample['age'] = res[4]
        sample['sex'] = res[5]
        sample['tissue'] = res[6]
        sample['source'] = res[7]
        sample['sourceDate'] = res[8]
        sample['soureType'] = res[9]
        sample['breedingDetails'] = res[10]
        sample['genotype'] = res[11]
        sample['misc'] = res[12]
        sample['disease'] = res[13]
        sampleList.append(sample)
    meta['samples']=sampleList

    protocolList = []
    cursor.execute(selectMetaProtocol + str(payload['datasetID'])+"))")
    results5 = cursor.fetchall()
    for res in results5:
        protocol = {}
        protocol['protocolID'] = res[0]
        protocol['title'] = res[1]
        protocol['description'] = res[2]
        protocol['version'] = res[3]
        protocol['protocolType'] = res[4]
        url=""
        if(not res[5] is None and not res[6] is None):
            url="https://phenogen.org"+res[6]+"/"+res[5]
        protocol['URL'] = url
        protocolList.append(protocol)
    meta['protocols'] = protocolList
    cursor.close()
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
        tmp['resultID'] = r[0]
        tmp['type'] = r[2]
        tmp['genomeVersion']=r[3]
        tmp['hrdpVersion'] = r[4]
        tmp['dateCreated'] = str(r[5])
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
                return(message,getHelp())
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