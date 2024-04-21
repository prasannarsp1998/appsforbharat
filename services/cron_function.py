from rq import Queue
import datetime
import pytz
import json
from services.startup import mysql_connection, redis_connection

redis_conn = redis_connection()
q = Queue(connection=redis_conn)


def daily_remainder():
    print("Job invoked")
    datetime_now = datetime.datetime.now(pytz.timezone("Asia/Kolkata")).strftime(
        "%Y-%m-%d"
    )
    mycursor, mydb = mysql_connection()
    mycursor.execute(
        "SELECT * FROM reminders WHERE date = %s and status = 'created'",
        (datetime_now,),
    )
    reminders = mycursor.fetchall()
    for reminder in reminders:
        print(reminder)
        # Connect to Redis
        redis_conn.publish(
            "afb",
            json.dumps(
                {
                    "toUser": reminder["user"],
                    "message": reminder["message"],
                    "id": reminder["id"],
                }
            ),
        )
        mycursor.execute(
            "UPDATE reminders SET status = 'triggered', datetime = JSON_SET(datetime, '$.triggeredAt', %s) WHERE id = %s",
            (
                str(
                    datetime.datetime.now(pytz.timezone("Asia/Kolkata")).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                ),
                reminder["id"],
            ),
        )
        mydb.commit()
    job = q.enqueue_in(datetime.timedelta(seconds=10), daily_remainder)
