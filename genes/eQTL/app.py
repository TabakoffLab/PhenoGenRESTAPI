import os,json,pymysql,boto3,logging
import MyDBConnection
logger = logging.getLogger()
logger.setLevel(logging.INFO)




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
    response = {}
    response['parameters'] = {}
    response['parameters']['gene'] = {
        "description": "Gene parameter - Required - This parameter is required to pull up a gene report.  This should correspond to a PhenoGen ID or an Affy Transcript Cluster ID of the gene."}
    response['parameters']['type'] = {
        "description": "Type parameter - This parameter specifies the data source to use.", "options": ["seq", "array"],
        "default": "seq"}
    response['parameters']['cutoff'] = {
        "description": "Cutoff parameter - This parameter specifies -log(Pvalue) cutoff to use the returned values must be >=cutoff.",
        "options": "any >1.0", "default": 2.0}
    response['parameters']['tissues'] = {
        "description": "Tissues parameter - This parameter specifies tissues to retreive eQTLs for as a comma seperated list. Options depend on source type.",
        "options": ["seq:Brain,Liver", "array:Brain,Heart,Liver,BAT"], "default": "Brain,Liver"}
    response['parameters']['genomeVersion'] = {
        "description": "GenomeVersion parameter - This parameter specifies genomeVersion to return results for.",
        "options": ["rn5", "rn6", "mm10"], "default": "rn6"}
    response['parameters']['version'] = {
        "description": "Version parameter - This parameter specifies the rna_dataset version to use for the results.  This corresponds to the version of the HRDP dataset.",
        "options": uniqueVersions, "default": "latest version"}
    return response


def lambda_handler(event, context):
    message = ""
    geneID = ""
    dataType = "seq"
    cutoff = 2.0
    tissueValidation = {"Brain": 1, "Liver": 1,"Kidney":1}
    tissues = "Brain,Liver,Kidney"
    genomeVer = "rn6"
    dataVersion = ""
    version = ""
    payload=None
    if('querystring' in event['params']):
        payload = event['params']['querystring']
    idType = ""
    newTissues = "'Brain','Liver','Kidney'"
    print("start")
    if (payload != None and payload != ""):
        if ('type' in payload):
            dataType = payload['type']
            if (dataType == "array"):
                tissues = "Brain,Heart,Liver,BAT"
                tissueValidation = {"Brain": 1, "Liver": 1, "Heart": 1, "BAT": 1}
                newTissues = "'Brain','Heart','Liver','Brown Adipose'"
        
        if ('gene' in payload):
            geneID = payload['gene']
            if (geneID.startswith("PRN") or (
                    geneID.isdigit() and len(geneID) == 7 and (geneID.startswith("7") or geneID.startswith("6")))):
                print("valid ID")
                if (geneID.startswith("PRN")):
                    idType = "PhenogenID"
                else:
                    idType = "AffyID"
            else:
                if (dataType == "seq"):
                    return respond(InputError('gene',
                                              'Gene Required - ?gene=PhenogenID - PhenoGen geneID required rest.phenogen.org/genes/idLookup provides appropriate id from other IDs.'))
                else:
                    return respond(InputError('gene',
                                              'Gene Required - ?gene=AffyID - Affy Transcript Cluster ID from Exon 1.0 ST arrays is required rest.phenogen.org/genes/idLookup provides appropriate id from other IDs.'))
        else:
            print("Gene Required")
            return respond(InputError('gene',
                                      'Gene Required - ?gene=PhenogenID - PhenoGen geneID(seq) or Affymetrix Transcript ClusterID(array) required rest.phenogen.org/genes/idLookup provides appropriate id from other IDs.'))
        
        if ('cutoff' in payload):
            cutoff = float(payload['cutoff'])
        
        if ('tissues' in payload):
            tissues = payload['tissues']
        if ('version' in payload):
            version = payload['version']
            if (geneID.find("RN6.") > 0):
                tmp = geneID[geneID.find(".") + 1:][0]
                print("version:" + tmp)
                tmpversion = str(int(tmp) - 1)
                if (version != tmpversion):
                    return respond(InputError('version/geneID',
                                              'Version and Gene ID don\'t agree. You provided version:' + version + ' while the gene ID matches version:' + tmpversion))
            else:
                if (version != "1"):
                    return respond(InputError('version/geneID',
                                              'Version and Gene ID don\'t agree. You provided version:' + version + ' while the gene ID matches version: 1'))
        # check ID for version
        if (geneID.find("RN6.") > 0):
            tmp = geneID[geneID.find(".") + 1:][0]
            print("version:" + tmp)
            version = str(int(tmp) - 1)
        else:
            version = "1"
        print("have params")
        tList = tissues.split(",")
        newTissues = ""
        TissueDS = ""
        for t in tList:
            if (not t in tissueValidation):
                message += " Tissue: " + t + " is invalid"
            else:
                # convert Brain to whole brain
                tmp = t
                if (t == "Brain"):
                    tmp = "Whole Brain"
                
                if (newTissues == ""):
                    TissueDS = "'" + t + "'"
                    newTissues = "'" + tmp + "'"
                else:
                    TissueDS += ",'" + t + "'"
                    newTissues += ",'" + tmp + "'"
        if ('genomeVersion' in payload):
            genomeVer = payload['genomeVersion']

        # sanity checks
        if (dataType == "seq"):
            if (idType == "PhenogenID"):
                message = "" + message
            else:
                message = "This appears to be an AffyID which is not valid for type:'seq'" + message
        
        elif (dataType == "array"):
            if (idType == "AffyID"):
                message = "" + message
            else:
                message = "This appears to be a PhenogenID which is not valid for type'array'. Please use /genes/idLookup to find the corresponding Affy transcript cluster id. " + message
        if (cutoff > 5):
            message += " Cutoff is likely too high to return results.  Valid range: 1.0-5.0"
        elif (cutoff < 1):
            message += " Cutoff is too low to return additional results. Valid range: 1.0-5.0"

        # get eQTLS
        eQTLList = []
        datasets = {}
        tissueVersions = {}
        
        ## Lookup LSE(locus_specifice_eqtl2) probe_id(gene name)
        cursorLookup = conn.cursor()
        dsQuery = "select rna_dataset_id,tissue,build_version from rna_dataset where strain_panel='BNLX/SHRH' and genome_id='" + genomeVer + "' and tissue in (" + TissueDS + ") and trx_recon=1 and visible=1 "
        if (version == ""):
            dsQuery = dsQuery + " order by build_version DESC"
        else:
            dsQuery = dsQuery + " and build_version= " + version
        print("sql:" + dsQuery)
        cursor = conn.cursor()
        cursor.execute(dsQuery)
        res = cursor.fetchmany()
        while (len(res) > 0):
            for r in res:
                if (not r[1] in datasets):
                    datasets[r[1]] = r[0]
                    tissueVersions[r[1]] = r[2]
            res = cursor.fetchmany()
        dataVersion = ""
        for v in datasets.keys():
            if (dataVersion == ""):
                dataVersion = str(datasets[v])
            else:
                dataVersion = dataVersion + "," + str(datasets[v])
        print("DV:" + dataVersion)
        ## run query
        lse_query = "select s.SNP_NAME, c.NAME, s.SNP_START, s.TISSUE, e.PVALUE from SNPs s, chromosomes c, Location_Specific_EQTL2 e where e.PROBE_ID = '" + geneID + "' and s.chromosome_id = c.chromosome_id and s.type='" + dataType + "' and e.SNP_ID = s.SNP_ID and s.genome_id='" + genomeVer + "' and e.pvalue >= " + str(
            cutoff)
        if (tissues.find(",") > -1):
            lse_query = lse_query + " and s.tissue in (" + newTissues + ")"
        else:
            lse_query = lse_query + " and s.tissue =" + newTissues
        if (dataType == "seq" and dataVersion != ""):
            if (dataVersion.find(",") > -1):
                lse_query = lse_query + " and s.rna_dataset_id in (" + dataVersion + ") "
            else:
                lse_query = lse_query + " and s.rna_dataset_id =" + dataVersion + " "
        cursor = conn.cursor()
        cursor.execute(lse_query)
        res = cursor.fetchmany()
        while (len(res) > 0):
            for r in res:
                tmp = {}
                tmp["SNP_ID"] = str(r[0])
                tmp["CHROMOSOME"] = r[1]
                tmp["SNP"] = str(r[2])
                tmp["TISSUE"] = r[3]
                tmp["NegLogPvalue"] = str(r[4])
                eQTLList.append(tmp)
            res = cursor.fetchmany()
        conn.close()
        resultDict = {
            "message": message,
            "parameters": {
                "Gene": geneID,
                "DataSource": dataType,
                "P-valueCutoff": cutoff,
                "Tissues": tissues,
                "GenomeVersion": genomeVer,
                "ResultCount": len(eQTLList),
                "Datasets": tissueVersions
            },
            "data": eQTLList}
        
        return respond(None, resultDict)
    else:
        print("get Help")
        return respond(None, getHelp(newTissues, genomeVer))


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