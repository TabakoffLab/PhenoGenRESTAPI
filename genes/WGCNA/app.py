import os, json, pymysql, boto3, logging
import MyDBConnection

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def respond(err, res=None):
  body = ""
  if err:
    if (res is not None):
      body = {"message": err.message, "help": json.dumps(res)}
    else:
      body = {"message": err.message}
  else:
    body = json.dumps(res)
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
  response['parameters']['gene'] = {
    "description": "Gene parameter - Required - This parameter is required to find modules containing the gene.  This should correspond to a PhenoGen ID or an Affy Transcript Cluster ID of the gene."}
  return response


def getWGCNADatasetID(tissue, panel, genomeVer, dataType, version, conn):
  wgcnaID = -1
  ret = []
  ds_query = "Select wdsid,rna_dataset_id from WGCNA_Dataset where tissue='" + tissue + "' and panel='" + panel + "' and genome_id='" + genomeVer + "' \
            and type='" + dataType + "' and visible=1"
  if (version == "LATEST"):
    ds_query += " order by version DESC"
  else:
    ds_query += " and version='" + version + "'"
  print(ds_query)
  cursor = conn.cursor()
  cursor.execute(ds_query)
  res = cursor.fetchone()
  if (cursor.rowcount > 0):
    print("res:" + str(res[0]) + ":" + str(res[1]))
    ret.append(int(res[0]))
    ret.append(int(res[1]))
  else:
    ret.append(-1)
    ret.append(-1)
  cursor.close()
  return ret


def getModuleList(geneID, dataType, panel, tissue, genomeVer, version, conn):
  wgcnaID = getWGCNADatasetID(tissue, panel, genomeVer, dataType, version, conn)
  message = ""
  if (wgcnaID[0] > 0):
    cursorLookup = conn.cursor()
    wgQuery = "Select distinct module_id,module,gene_id from wgcna_module_info where wdsid=" + str(
      wgcnaID[0]) + " and gene_id='" + geneID + "' order by module_id"
    print(wgQuery + "\n")
    moduleList = []
    moduleDict = {}
    ## run query
    
    cursorLookup.execute(wgQuery)
    res = cursorLookup.fetchmany()
    while (len(res) > 0):
      for r in res:
        if (r[0] in moduleDict):
          moduleDict[r[0]]["Gene_List"].append(r[2])
        else:
          tmp = {}
          tmp["Module_ID"] = str(r[0])
          tmp["Module_Name"] = r[1]
          tmp["Gene_List"] = [r[2]]
          moduleList.append(tmp)
          moduleDict[r[0]] = tmp
      res = cursorLookup.fetchmany()
    cursorLookup.close()
    modListString = ""
    modQueryPart = ""
    for m in moduleList:
      if (modListString == ""):
        modListString = str(m["Module_ID"])
      else:
        modListString = modListString + "," + str(m["Module_ID"])
    if (modListString.find(",") > 0):
      modQueryPart = " in (" + modListString + ") "
    else:
      modQueryPart = "= " + modListString
    print(modQueryPart + "\n")
    cursorLookup = conn.cursor()
    if (len(moduleList) > 0):
      wgQuery2 = "Select distinct module_id,module,gene_id from wgcna_module_info where wdsid=" + str(
        wgcnaID[0]) + " and module_id " + modQueryPart + " order by module_id"
      ## run query
      print(wgQuery2 + "\n")
      cursorLookup.execute(wgQuery2)
      res = cursorLookup.fetchmany()
      while (len(res) > 0):
        for r in res:
          if (r[0] in moduleDict):
            moduleDict[r[0]]["Gene_List"].append(r[2])
        res = cursorLookup.fetchmany()
    else:
      message = "No modules found."
    conn.close()
    resultDict = {
      "message": message,
      "parameters": {
        "Gene": geneID,
        "DataSource": dataType,
        "Tissue": tissue,
        "GenomeVersion": genomeVer,
        "Version": version,
        "WGCNADatasetID": wgcnaID[0]
      },
      "data": moduleList}
    return respond(None, resultDict)
  else:
    return respond(InputError("No WGCNA Dataset", "No WGCNA Dataset was found with the specified parameters."))


def getModuleData(wgcnaID, moduleID, moduleName, dataType, panel, tissue, genomeVer, version, conn):
  if (int(wgcnaID) < 0):
    wgcnaID = getWGCNADatasetID(tissue, panel, genomeVer, dataType, version, conn)
  if (int(wgcnaID) > 0):
    return respond(
      InputError("Not Yet Implemented", "This function is not yet fully implemented Please check back mid Sept 2019"))
  else:
    return respond(InputError("No WGCNA Dataset", "No WGCNA Dataset was found with the specified parameters."))


def lambda_handler(event, context):
  message = ""
  geneID = ""
  dataType = "seq"
  panel = "BNLx/SHR"
  tissue = "Whole Brain"
  genomeVer = "rn6"
  version = "LATEST"
  wgcnaID = -1
  rnaDSID = -1
  moduleName = ""
  moduleID = ""
  moduleDatatype = ""
  payload=None
  if('querystring' in event['params']):
    payload = event['params']['querystring']
  
  if (payload != None):
    if ('gene' in payload):
      geneID = payload['gene']
    if ('type' in payload):
      dataType = payload['type']
    if ('tissue' in payload):
      tissue = payload['tissue']
    if ('genomeVersion' in payload):
      genomeVer = payload['genomeVersion']
    if ('version' in payload):
      version = payload['version']
    if ('moduleID' in payload):
      moduleID = payload['moduleID']
    if ('moduleName' in payload):
      moduleName = payload['moduleName']
    if ('wgcnaID' in payload):
      wgcnaID = payload['wgcnaID']
    if ('moduleDatatype' in payload):
      moduleName = payload['moduleDatatype']
    
    # get WGCNA Modules
    conn = MyDBConnection.ConnectDB()
    
    if (moduleID == "" and moduleName == "" and geneID != ""):
      return getModuleList(geneID, dataType, panel, tissue, genomeVer, version, conn)
    elif (moduleID != "" or moduleName != ""):
      return getModuleData(wgcnaID, moduleID, moduleName, dataType, panel, tissue, genomeVer, version, conn)
    else:
      return respond(None, getHelp())
  else:
    return respond(None, getHelp())


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