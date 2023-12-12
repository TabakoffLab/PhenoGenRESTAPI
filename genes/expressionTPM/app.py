import logging
import MyDBConnection, SharedUtilityFunctions

logger = None
functionPath="genes/expressionTPM"



def getHelp(tissueList, gVer):
    conn = MyDBConnection.ConnectDB()
    cursorLookup = conn.cursor()
    helpQuery = "select distinct build_version from rna_dataset where strain_panel='BNLX/SHRH' and genome_id='" + gVer + "' and tissue in (" + tissueList + ") and trx_recon=1 and visible=1 "
    cursor = conn.cursor()
    cursor.execute(helpQuery)
    res = cursor.fetchmany()
    uniqueVersions = []
    while (len(res) > 0):
        for r in res:
            uniqueVersions.append(r[0])
        res = cursor.fetchmany()
    response = SharedUtilityFunctions.getHelpMain()
    response['parameters']['gene'] = {
        "description": "Gene parameter - Required - This parameter is required to pull up a gene report.  This should correspond to a PhenoGen ID or an Affy Transcript Cluster ID of the gene."}
    response['parameters']['type'] = {
        "description": "Type parameter - This parameter specifies the data source to use.", "options": ["seq", "array"],
        "default": "seq"}

    response['parameters']['tissues'] = {
        "description": "Tissues parameter - This parameter specifies tissues to retreive eQTLs for as a comma seperated list. Options depend on source type.",
        "options": ["seq:Brain,Liver,Heart,Kidney"], "default": "Brain,Liver"}
    response['parameters']['genomeVersion'] = {
        "description": "GenomeVersion parameter - This parameter specifies genomeVersion to return results for.",
        "options": ["rn7","rn6", "rn5", "mm10"], "default": "rn7"}
    response['parameters']['version'] = {
        "description": "Version parameter - This parameter specifies the rna_dataset version to use for the results.  This corresponds to the version of the HRDP dataset.",
        "options": uniqueVersions, "default": "latest version"}
    return response


def lambda_handler(event, context):
    logger=SharedUtilityFunctions.setupLog()
    ip = event['context']['source-ip']
    SharedUtilityFunctions.sendSQSMessage(functionPath, ip)
    message = ""
    geneID = ""
    dataType = "seq"
    cutoff = 2.0
    tissueValidation = {"Brain": 1, "Liver": 1,"Kidney":1,"Heart":1}
    tissues = "Brain,Liver,Kidney,Heart"
    genomeVer = "rn7"
    dataVersion = ""
    version = ""
    payload=None
    if('querystring' in event['params']):
        payload = event['params']['querystring']
    idType = ""
    newTissues = "'Brain','Liver','Kidney','Heart'"
    print("start")
    if (payload != None and payload != ""):

        
        return SharedUtilityFunctions.respond(None, resultDict)
    else:
        print("get Help")
        return SharedUtilityFunctions.respond(None, getHelp(newTissues, genomeVer))


