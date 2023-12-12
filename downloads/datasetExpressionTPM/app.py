import logging, boto3, os, json
import MyDBConnection, SharedUtilityFunctions, datasetLib

logger = SharedUtilityFunctions.setupLog()
functionPath = "downloads/datasetExpressionTPM"


def getHelp():
    response = SharedUtilityFunctions.getHelpMain()
    response['parameters']['datasetID'] = {
        "description": "datasetID parameter - Required - ID of the dataset to retrieve."}
    return response


def lambda_handler(event, context):
    operation = 'GET'
    message = ""
    (logger, operation) = SharedUtilityFunctions.setup(event, functionPath, operation)

    if operation == 'GET':
        payload = None
        annotation = ""
        analysisLevel = ""
        tissue = ""
        version = ""
        genomeVersion = ""
        strainMeans = 0
        resultType = "Quantification - TPM%"
        conn = None
        ds = None
        if ('querystring' in event['params']):
            payload = event['params']['querystring']
        if 'help' in payload:
            return SharedUtilityFunctions.respond(None, getHelp())
        else:
            if "annotation" in payload:
                annotation = payload['annotation']
            else:
                message = "missing required parameter:annotation"
                return SharedUtilityFunctions.respond(SharedUtilityFunctions.InputError("MissingParameter", message),
                                                      getHelp())
            if "analysisLevel" in payload:
                analysisLevel = payload['analysisLevel']
            else:
                message = "missing required parameter:analysisLevel"
                return SharedUtilityFunctions.respond(SharedUtilityFunctions.InputError("MissingParameter", message),
                                                      getHelp())
            if "tissue" in payload:
                tissue = payload['tissue']
            else:
                message = "missing required parameter:tissue"
                return SharedUtilityFunctions.respond(SharedUtilityFunctions.InputError("MissingParameter", message),
                                                      getHelp())
            if "strainMeans" in payload:
                strainMeans = payload['strainMeans']
            if "version" in payload:
                version = payload['version']
            if "genomeVersion" in payload:
                genomeVersion = payload['genomeVersion']
            conn = MyDBConnection.ConnectDB()
            ds = datasetLib.getDatasetByParams(conn, annotation, analysisLevel, tissue, strainMeans, version,
                                               genomeVersion, resultType, logger)
            conn.close()
        return SharedUtilityFunctions.respond("", SharedUtilityFunctions.formatResponse("", ds))
    else:
        return SharedUtilityFunctions.respond(SharedUtilityFunctions.InputError('HTTPMethod', 'Unsupported method'),
                                              getHelp())