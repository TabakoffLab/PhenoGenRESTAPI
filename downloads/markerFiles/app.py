import os,  boto3
import MyDBConnection,SharedUtilityFunctions


selectDataset="select * from inia_prod.misc_download_files"

def getHelp():
    response = SharedUtilityFunctions.getHelpMain()
    response['parameters']['markerSetID'] = {
        "description": "markerSetID parameter - Required parameter to get files for the selected Marker Data Set."
    }
    return response



def getMarkerFiles(conn,payload):
    ds=[]
    cursor=conn.cursor()
    query=selectDataset
    markerID=0
    if (payload != None and payload != ""):
        query = query + " where download_group_id=" + payload['markerSetID']
    cursor.execute(query)
    res = cursor.fetchmany()
    while (len(res)):
        for r in res:
            tmp={}
            tmp['download_file_id']=r[0]
            tmp['marker_set_id'] = r[1]
            tmp['description']=r[2]
            tmp['filename']=r[3]
            tmp['checksum']=r[4]
            tmp['URL']=r[5]
            ds.append(tmp)
        res = cursor.fetchmany()
    cursor.close()
    return ds

def lambda_handler(event, context):
    SharedUtilityFunctions.setupLog()
    operation = 'GET'
    if ('httpMethod' in event):
        operation = event['httpMethod']
    message = ""
    if operation == 'GET':
        payload = None
        if 'params' in event and 'querystring' in event['params']:
            payload = event['params']['querystring']
        if payload is None or not 'markerSetID' in payload:
            return SharedUtilityFunctions.respond(SharedUtilityFunctions.ParameterMissingError("markerSetID","required parameter missing"),getHelp())
        elif payload is not None and 'help' in payload:
            return SharedUtilityFunctions.respond(None,getHelp())
        else:
            conn = MyDBConnection.ConnectDB()
            datasets=getMarkerFiles(conn,payload)
            conn.close()
            results=SharedUtilityFunctions.formatResponse(message,datasets)
            return SharedUtilityFunctions.respond(None, results)
    else:
        return SharedUtilityFunctions.respond(InputError("HTTPMethod","Unsupported Method"),getHelp())


