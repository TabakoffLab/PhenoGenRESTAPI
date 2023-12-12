import os,json
import MyDBConnection,SharedUtilityFunctions

selectDataset="select * from rna_dataset2"

logger=None
functionPath="downloads/datasets"



def getHelp():
    response = SharedUtilityFunctions.getHelpMain()
    response['parameters']['genomeVer'] = {
        "description": "genomeVer parameter - Optional parameter to filter results to a specific genome version."}
    response['parameters']['organism'] = {
        "description": "organism parameter - Optional parameter to filter results to a specific organism", "options": ["Rn", "Mm"]
    }
    response['parameters']['panel'] = {
        "description": "panel parameter - Optional parameter to filter results to a specific panel of animals."}
    response['parameters']['type'] = {
        "description": "type parameter - Optional parameter to filter results to a specific sequencing type.","options":["smallRNA","totalRNA"]}
    response['parameters']['tissue'] = {
        "description": "tissue parameter - Optional parameter to filter results to a specific tissue. Note: Please use Brain instead of 'Whole Brain'"}
    return response


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
            tmp['datasetID']=r[0]
            tmp['organism']=r[1]
            tmp['panel']=r[3]
            tmp['description']=r[4]
            tmp['created']=str(r[6])
            tmp['tissue']=r[8]
            tmp['SeqType']=r[9]
            tmp['GenomeVer']=r[10]
            ds.append(tmp)
        res = cursor.fetchmany()
    cursor.close()
    return ds

def lambda_handler(event, context):
    operation = 'GET'
    message = ""
    (logger, operation) = SharedUtilityFunctions.setup(event, functionPath, operation)
    
    if operation == 'GET':
        payload = None
        if ('querystring' in event['params']):
            payload = event['params']['querystring']
        if 'help' in payload:
            return SharedUtilityFunctions.respond(None,getHelp())
        else:
            conn = MyDBConnection.ConnectDB()
            datasets=getDatasets(conn,payload)
            conn.close()
            results=SharedUtilityFunctions.formatResponse(message,datasets)
            return SharedUtilityFunctions.respond(None, results)
    else:
        return SharedUtilityFunctions.respond(SharedUtilityFunctions.InputError("HTTPMethod","Unsupported Method"),getHelp())

