import os, json, pymysql, logging
import boto3, MyDBConnection
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def getHelp(conn):
  targetList = getTargetValues(conn).keys()
  newList = []
  for t in targetList:
    newList.append(str(t))
  response = {}
  response['parameters'] = {}
  response['parameters']['gene'] = {"description": "Gene parameter - Required - Any supported Gene ID"}
  response['parameters']['organism'] = {
    "description": "Organism parameter - This parameter specifies the species to use to find the ID specified.",
    "options": ["Rn", "Mm", "Hs"], "default": "Rn"}
  response['parameters']['alevel'] = {
    "description": "alevel parameter - This parameter specifies the number of links between IDs to traverse.  Due to potential confusion between aliases of genes we recommend keeping this low(<=2) to minimize false positives.  However some combinations of IDs/Targets will require a higher value.",
    "options": "integers 0-10", "default": 1}
  response['parameters']['targetList'] = {
    "description": "targetList parameter - This parameter specifies ID Types of interest and limits results to IDs of the specified type(s).  Comma seperated list of target IDs.",
    "options": newList, "default": "No Target Filter"}
  return response


def respond(err, res=None):
  return {
    'statusCode': '400' if err else '200',
    'body': err.message if err else json.dumps(res),
    'headers': {
      'Content-Type': 'application/json'
    },
    "isBase64Encoded": False
  }


def getTargetValues(conn):
  ret = {}
  query = "select name from identifier_types"
  cursor = conn.cursor()
  cursor.execute(query)
  res = cursor.fetchmany()
  while (len(res)):
    for r in res:
      ret[r[0]] = 1
    res = cursor.fetchmany()
  cursor.close()
  return ret


def lambda_handler(event, context):
  operation = 'GET'
  if('httpMethod' in event):
    operation=event['httpMethod']
  message = ""
  if operation == 'GET':
    conn = MyDBConnection.ConnectDB()
    alevel = 1
    organism = 'Rn'
    targetList = ''
    IDs = []
    payload=None
    if('queryStringParameters' in event):
      payload = event['queryStringParameters']
      
    if (payload != None):
      if ('gene' in payload):
        
        targetValidation = getTargetValues(conn)
        geneID = payload['gene']
        if ('organism' in payload):
          organism = payload['organism']
        if ('level' in payload):
          alevel = payload['level']
        if ('targetList' in payload):
          targetList = payload['targetList'].split(",")
          newTargetList = ""
          for t in targetList:
            if (not t in targetValidation):
              message += " Target: " + t + " is invalid"
            else:
              if (newTargetList == ""):
                newTargetList = "'" + t + "'"
              else:
                newTargetList += ",'" + t + "'"
        
        ## Lookup LSE(locus_specifice_eqtl2) probe_id(gene name)
        lse_query = "select idl.level,idt.name,id2.* from identifiers id1 \
                      left outer join id_lookup idl on id1.ID_NUMBER=idl.ID1_NUMBER \
                      left outer join identifiers id2 on id2.ID_NUMBER=idl.ID2_NUMBER \
                      left outer join identifier_types idt on id2.ident_type_id=idt.ident_type_id\
        		      where \
        		      id1.identifier = '" + geneID + "' \
        		      and idl.organism = '" + organism + "'\
        		      and idl.level <= " + str(alevel)
        if (targetList != ""):
          lse_query = lse_query + " and idt.name in (" + newTargetList + ")";
        cursor = conn.cursor()
        cursor.execute(lse_query)
        res = cursor.fetchmany()
        while (len(res)):
          for r in res:
            tmp = {}
            tmp["ID_LEVEL"] = str(r[0])
            tmp["ID_TARGET"] = r[1]
            tmp["ORGANISM"] = r[3]
            tmp["ID"] = r[5]
            tmp["CHR"] = r[6]
            tmp["CM"] = r[7]
            tmp["START"] = r[8]
            tmp["STOP"] = r[9]
            tmp["STRAND"] = r[10]
            IDs.append(tmp)
          res = cursor.fetchmany()
        conn.close()
        resultDict = {
          "message": message,
          "parameters": {
            "Gene": geneID,
            "Organism": organism,
            "Level": alevel,
            "TargetList": targetList,
            "ResultCount": len(IDs)
          },
          "data": IDs}
        return respond(None, resultDict)
      else:
        return respond(
          InputError("Missing Parameter", "gene is a required parameter.  Call with no parameters for Help."))
    else:
      return respond(None, getHelp(conn))
  else:
    return respond(InputError('HTTPMethod', 'Unsupported method ' + format(operation)))


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
