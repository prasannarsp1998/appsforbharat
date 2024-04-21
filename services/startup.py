import redis
import json
import config
import boto3
import mysql.connector
import datetime
import pytz


# database connection
def mysql_connection():
    mydb = mysql.connector.connect(
        host=config.config["DB_HOST"],
        user=config.config["DB_USER"],
        password=config.config["DB_PASSWORD"],
        database=config.config["DB_NAME"],
    )
    mycursor = mydb.cursor(dictionary=True)
    return mycursor, mydb


def redis_connection():
    redis_conn = redis.StrictRedis(host=config.config["REDIS_HOST"], port=6379, db=0)
    return redis_conn


# On startup create new table `reminders` in the database
def create_table():
    mycursor, mydb = mysql_connection()
    mycursor.execute(
        "CREATE TABLE IF NOT EXISTS reminders (id INT AUTO_INCREMENT PRIMARY KEY, message TEXT, date DATE, status VARCHAR(255), datetime JSON, user VARCHAR(255))"
    )
    mydb.commit()
    mycursor.close()
    mydb.close()


# Function to listen to Redis and send email
def listen_to_redis():
    print("Listening to Redis")
    redis_conn = redis_connection()
    pubsub = redis_conn.pubsub()
    pubsub.subscribe("afb")
    while True:  # Infinite loop to keep listening
        message = pubsub.get_message()
        if message and message["type"] == "message":
            print("Email block")
            mess = json.loads(message["data"].decode("utf-8"))
            try:
                client = boto3.client(
                    "ses",
                    region_name=config.config["AWS_REGION"],
                    aws_access_key_id=config.config["AWS_IAM_USER"],
                    aws_secret_access_key=config.config["AWS_IAM_SECR"],
                )
                response = client.send_email(
                    Source=config.config["AWS_SES_SENDER_EMAIL"],
                    Destination={"ToAddresses": [mess["toUser"]]},
                    Message={
                        "Subject": {"Data": "Reminder from AppsForBharat"},
                        "Body": {"Text": {"Charset": "UTF-8", "Data": mess["message"]}},
                    },
                )
                mycursor, mydb = mysql_connection()
                mycursor.execute(
                    "update reminders set status = 'sent', datetime = JSON_SET(datetime, '$.emailedAt', %s) where id = %s",
                    (
                        str(
                            datetime.datetime.now(
                                pytz.timezone("Asia/Kolkata")
                            ).strftime("%Y-%m-%d %H:%M:%S")
                        ),
                        mess["id"],
                    ),
                )
                mydb.commit()
                mycursor.close()
                mydb.close()
            except Exception as e:
                print(e)
                print("Error while sending Reminder EMAIL via AWS SES")
