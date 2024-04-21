import datetime
import json
import re
from dateutil import parser
import pytz
import config
from services.startup import redis_connection, mysql_connection


def create_reminder(event, user_email):
    # Check if JWT token present

    try:
        # make sure reminderData key is present
        if "reminder_data" not in event:
            return (
                {
                    "response": "failure",
                    "message": '"reminder_data" key is missing',
                },
                400,
            )

        # initialize datetime with indian timezone
        datetime_now = datetime.datetime.now(pytz.timezone("Asia/Kolkata")).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # split reminder text and date string by 'on'
        reminder, dateString = re.split(
            r"\bon\b", event["reminder_data"], flags=re.IGNORECASE
        )

        # remove extra spaces
        reminder = reminder.strip()

        # pass dateString to date parser to get meaningful date
        try:
            parsed_date = parser.parse(dateString, fuzzy=True)
        except ValueError:
            return {"response": "failure", "message": "Invalid Date"}, 400

        parsed_date = parsed_date.replace(tzinfo=pytz.timezone("Asia/Kolkata"))
        if (
            parsed_date.date()
            < datetime.datetime.now(pytz.timezone("Asia/Kolkata")).date()
        ):
            return {
                "response": "failure",
                "message": "Cannot create Reminder for past dates",
            }, 400
        mycursor, mydb = mysql_connection()
        mycursor.execute(
            "insert into reminders (message, date, status, datetime, user) values (%s, %s, %s, %s, %s)",
            (
                reminder,
                parsed_date,
                "created",
                json.dumps(
                    {
                        "createdAt": str(datetime_now),
                        "triggeredAt": None,
                        "deletedAt": None,
                        "emailedAt": None,
                    }
                ),
                user_email,
            ),
        )
        mydb.commit()
        mycursor.close()
        mydb.close()
        return {"response": "success"}, 201
    except Exception as e:
        print(e)
        return {"response": "failure", "message": "Internal Server Error"}, 500


def delete_reminder(user_email, reminder_id):
    try:
        datetime_now = datetime.datetime.now(pytz.timezone("Asia/Kolkata")).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        mycursor, mydb = mysql_connection()
        mycursor.execute("select * from reminders where id = %s", ((reminder_id,)))
        is_exists = mycursor.fetchone()

        if not is_exists:
            return ({"response": "failure", "message": "Reminder not found"}, 404)
        elif is_exists["user"] != user_email:
            return ({"response": "failure", "message": "Unauthorized"}, 401)
        elif is_exists["status"] != "created":
            return (
                {
                    "response": "failure",
                    "message": "Cannot delete already executed/deleted item",
                },
                400,
            )

        mycursor.execute(
            "update reminders set status = 'deleted', datetime = JSON_SET(datetime, '$.deletedAt', %s) where id = %s",
            (str(datetime_now), reminder_id),
        )
        mydb.commit()
        mycursor.close()
        mydb.close()
        return {}, 204
    except Exception as e:
        print(e)
        return {"response": "failure", "message": "Internal Server Error"}, 500


def fetch_reminders(page, per_page, status, user_email):
    try:

        offset = (page - 1) * per_page
        # Redis cache key for pagination
        cache_key = f"cached_data:{user_email}:{page}:{per_page}"

        # Check Redis cache first
        redis_conn = redis_connection()
        cached_data = redis_conn.get(cache_key)
        if cached_data:
            return {
                "response": json.loads(cached_data.decode("utf-8")),
                "page": page,
                "per_page": per_page,
            }, 200

        mycursor, mydb = mysql_connection()
        mycursor.execute(
            "select * from reminders where user = %s and ('all' IN (%s) OR status IN (%s)) limit %s offset %s",
            (user_email, status, status, per_page, offset),
        )
        response = []
        for reminder in mycursor.fetchall():
            reminder["date"] = str(reminder["date"])
            reminder["datetime"] = json.loads(reminder["datetime"])
            response.append(reminder)

        redis_conn.setex(cache_key, 60, json.dumps(response))  # Cache for 60 seconds
        mycursor.close()
        mydb.close()
        return {"response": response, "page": page, "per_page": per_page}, 200
    except Exception as e:
        print(e)
        return ({"response": "failure", "message": "Internal Server Error"}, 500)
