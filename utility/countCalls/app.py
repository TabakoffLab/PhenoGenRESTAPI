import os,datetime
import MyDBConnection,SharedUtilityFunctions

selectSQL="select count from rest_api_usage where function_name =%s FOR UPDATE"
updateSQL="Update rest_api_usage set count= %s where function_name=%s"
insertSQL_count="insert into rest_api_usage (function_name,count) VALUE(%s,%s)"
insertSQL_log="insert into rest_api_log (called_at,called_by_ip,function_name) VALUES (%s,%s,%s)"
def lambda_handler(event, context):

    logging=SharedUtilityFunctions.setupLog()

    conn = MyDBConnection.ConnectDBWOAutoCommit()
    textMsg=""
    code=400
    for message in event['Records']:
        print(message['body'])
        ip=message['messageAttributes']['IP']['stringValue']
        date=message['messageAttributes']['DATE']['stringValue']
        path=message['body']
        # Delete received message from queue
        logging.info("ip:"+ip+":"+date+":"+path)

        cursor = conn.cursor()
        cursor.execute(selectSQL,path)
        res = cursor.fetchone()
        print(res)
        if(res and res[0]):
            count = int(res[0])
            count=count+1
            cursor.execute(updateSQL,(count,path))
        else:
            cursor.execute(insertSQL_count,(path,1))
        conn.commit()
        newdt= datetime.datetime.strptime(date, '%d/%m/%Y %H:%M:%S')
        cursor.execute(insertSQL_log,(newdt,ip,path))
        cursor.close()
        conn.commit()

    conn.close()
    code=200

    return {
        'statusCode': code,
        'body': textMsg
    }


