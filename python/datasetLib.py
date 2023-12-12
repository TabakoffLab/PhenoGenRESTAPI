selectDatasetByID="SELECT * FROM rna_dataset2 where rna_dataset_id="

selectResultsByID="SELECT * FROM rna_dataset_results where rna_dataset_id="

selectFileByDatasetResultParams1="select * from rna_dataset_results_files where rna_dataset_result_id in (select rna_dataset_result_id from rna_dataset_results where result_type like '"
selectFileByDatasetResultParams2=" and annotation like '"
selectFileByDatasetResultParams3=" and level='"
selectFileByDatasetResultParams4=" and ISSTRAINMEANS="
selectFileByDatasetResultParams5=" and rna_dataset_id in (select rna_dataset_id from rna_dataset2 where tissue='"
selectFileByDatasetResultParams6=" )"
selectFileByDatasetResultParams7=" ) order by uploaded DESC"
optionGenomeVersion=" and genomeVersion='"
optionVersion =" and description like 'HRDP v"


def getDatasetByID(conn,id,logger):
    ds={}
    cursor=conn.cursor()
    query=selectDatasetByID+str(id)
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


def getDatasetByParams(conn,annotation,analysisLevel,tissue,strainMeans,version,genomeVersion,resultType,logger):
    if tissue=="Brain":
        tissue="Whole Brain"
    ds = {}
    cursor = conn.cursor()
    query = selectFileByDatasetResultParams1+resultType+"'"
    query = query+selectFileByDatasetResultParams2+annotation+"%'"+selectFileByDatasetResultParams3+analysisLevel+"'"
    query= query+selectFileByDatasetResultParams4+str(strainMeans)+selectFileByDatasetResultParams5+tissue+"'"
    if(genomeVersion != ""):
        query=query+optionGenomeVersion+genomeVersion+"'"
    query= query+selectFileByDatasetResultParams6
    if(version !=""):
        query=query+optionVersion+version+"'"
    query=query+selectFileByDatasetResultParams7
    logger.info(query)
    cursor.execute(query)
    res = cursor.fetchone()
    if res is not None:
        ds['datasetResultFileID'] = res[0]
        ds['uploaded'] = str(res[2])
        ds['filename'] = res[4]
        ds['URL'] = "https://phenogen.org/web/sysbio/downloadLink.jsp?url="+res[5]+res[3]
        ds['checksum'] = res[6]
        ds['genome_version'] = res[8]
        ds['description'] = res[9]
        ds['annotation'] = res[10]
        ds['level']=res[11]
        ds['isstrainmeans']=str(res[12])
    cursor.close()
    return ds