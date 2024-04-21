from flask import Flask, request, jsonify, make_response
import jwt
import redis
import config
import threading
from rq import Queue
import re

from services.cron_function import daily_remainder
from services.reminder import create_reminder, delete_reminder, fetch_reminders
from services.startup import create_table, listen_to_redis

app = Flask(__name__)


def validate_api(token):
    # logic to check signature of token or validity of the token
    # TODO - Verify valid EMAIL
    try:
        user_email = jwt.decode(
            token,
            algorithms=["HS256"],
            options={"verify_signature": False},
        )["user"]
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if re.match(pattern, user_email):
            return 200, user_email
        else:
            return 401, None
    except:
        return 401, None


@app.route("/reminders/create", methods=["POST", "OPTIONS"])
def api_reminder_create():
    if request.method == "OPTIONS":  # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "POST":
        if "Authorization" not in request.headers:
            return (
                _corsify_actual_response(
                    jsonify(
                        {
                            "response": "failure",
                            "message": "Missing JWT Token in Header",
                        }
                    )
                ),
                401,
            )
        # Check if JWT token is valid
        status_code, user_email = validate_api(
            request.headers["Authorization"].split(" ")[1]
        )

        if status_code == 401:
            return (
                _corsify_actual_response(
                    jsonify({"response": "failure", "message": "In-valid Token"})
                ),
                401,
            )
        response, status_code = create_reminder(request.json, user_email)
        return _corsify_actual_response(jsonify(response)), status_code
    else:
        # return 405 if method not allowed
        return (
            _corsify_actual_response(
                jsonify({"response": "failure", "message": "Method Not Allowed"})
            ),
            405,
        )


@app.route("/reminders/delete/<int:id>", methods=["DELETE", "OPTIONS"])
def api_reminder_delete(id):
    if request.method == "OPTIONS":  # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "DELETE":
        if "Authorization" not in request.headers:
            return (
                _corsify_actual_response(
                    jsonify(
                        {
                            "response": "failure",
                            "message": "Missing JWT Token in Header",
                        }
                    )
                ),
                401,
            )

        status_code, user_email = validate_api(
            request.headers["Authorization"].split(" ")[1]
        )

        if status_code == 401:
            return (
                _corsify_actual_response(
                    jsonify({"response": "failure", "message": "In-valid Token"})
                ),
                401,
            )
        print(user_email, id)
        response, status_code = delete_reminder(user_email, id)
        return _corsify_actual_response(jsonify(response)), status_code

    else:
        return (
            _corsify_actual_response(
                jsonify({"response": "failure", "message": "Method Not Allowed"})
            ),
            405,
        )


@app.route("/reminders", methods=["GET", "OPTIONS"])
def api_reminder_fetch():
    if request.method == "OPTIONS":  # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "GET":
        if "Authorization" not in request.headers:
            return (
                _corsify_actual_response(
                    jsonify(
                        {
                            "response": "failure",
                            "message": "Missing JWT Token in Header",
                        }
                    )
                ),
                401,
            )
        status_code, user_email = validate_api(
            request.headers["Authorization"].split(" ")[1]
        )

        if status_code == 401:
            return (
                _corsify_actual_response(
                    jsonify({"response": "failure", "message": "In-valid Token"})
                ),
                401,
            )
        page = int(request.args.get("page", 1))  # Default page 1
        per_page = int(request.args.get("per_page", 10))  # Default 10 items per page
        status = request.args.get("status", "all")  # Default status all
        response, status_code = fetch_reminders(page, per_page, status, user_email)
        return _corsify_actual_response(jsonify(response)), status_code
    else:
        return (
            _corsify_actual_response(
                jsonify({"response": "failure", "message": "Method Not Allowed"})
            ),
            405,
        )


def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response


def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


if __name__ == "__main__":

    redis_thread = threading.Thread(target=listen_to_redis)
    redis_thread.start()
    create_table()
    daily_remainder()
    app.run(host="0.0.0.0", port=678, debug=False)
