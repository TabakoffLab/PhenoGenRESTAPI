import os,  boto3
import MyDBConnection,SharedUtilityFunctions


selectDataset="select * from misc_download_groups"

def getHelp():
    response = SharedUtilityFunctions.getHelpMain()
    response['parameters']['genome_version'] = {
        "description": "genome_version parameter - Optional parameter to filter results to a specific genome version."}
    response['parameters']['organism'] = {
        "description": "organism parameter - Optional parameter to filter results to a specific organism", "options": ["Rn", "Mm"]
    }
    return response



def getMarkerSets(conn,payload):
    ds=[]
    cursor=conn.cursor()
    query=selectDataset
    type="Marker"

    if payload is not None and payload != "":
        query = query + " where type='" + type + "'"
        if 'genome_version' in payload:
            query = query + " and genomever='" + payload['genome_version'] + "'"
        if 'organism' in payload:
            query = query+" and organism='"+payload['organism']+"'"
            
    cursor.execute(query)
    res = cursor.fetchmany()
    while len(res):
        for r in res:
            tmp={
            "download_group_id":r[0],
            "display_name":r[1],
            "organism":r[2],
            "genome_version":r[3],
            "panel":r[4],
            "description":r[5],
            "type":r[6]
            }
            ds.append(tmp)
        res = cursor.fetchmany()
    cursor.close()
    return ds

def lambda_handler(event, context):
    SharedUtilityFunctions.setupLog()
    operation = 'GET'
    if 'httpMethod' in event:
        operation = event['httpMethod']
    message = ""
    if operation == 'GET':
        payload = None
        if 'params' in event and 'querystring' in event['params']:
            payload = event['params']['querystring']
        if payload is not None and 'help' in payload:
            return SharedUtilityFunctions.respond(None,getHelp())
        else:
            conn = MyDBConnection.ConnectDB()
            datasets=getMarkerSets(conn,payload)
            conn.close()
            results=SharedUtilityFunctions.formatResponse(message,datasets)
            return SharedUtilityFunctions.respond(None, results)
    else:
        return SharedUtilityFunctions.respond(InputError("HTTPMethod","Unsupported Method"),getHelp())


