# AppsForBharat Solution by Prasanna Sundaram

## Problem Statement

The task is to create a REST API webserver to handle reminders.

## Solution
The solution is implemented using Python Flask, MySQL and the main file is app.py. Solution is converted to a Docker File for easier testing.


## Technologies Used
- Python Flask
- Redis
- MySQL
- AWS SES (for email)
- Python RQ (for cronjob using redis)
- JWT

## Steps to run the project
1. Install Docker, Postman or any other API testing tool.
2. From the command line inside project directory run `docker-compose build` for building the docker file.
3. Then run `docker-compose up`.
4. After few seconds, Flask application is exposed in `http://127.0.0.1:678` URL.
5. Endpoints : 
   * Create Reminder:
     * URL - `http://127.0.0.1:678/reminders/create`
     * Method - `POST`
     * Request Body - `{"reminder_data":"Buy groceries on 20 April 2024"}`
     * Header - `Authorization <jwt token without signature>` (`user` key is mandatory in jwt payload data with valid email address which is used for storing/sending reminder email)
     * Example CURL - `curl --location 'http://127.0.0.1:678/reminders/create' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJ1c2VyIjoicHJhc2FubmFzY29ycGlhbkBnbWFpbC5jb20ifQ.8eG-dXsnzaGf0t57tpu2mcuvW4asOVa9470KNynIG4U' \
--data '{
    "reminder_data":"Buy groceries on 20 April 2024"
}'`
   * Delete Reminder:
     * URL - `http://127.0.0.1:678/reminders/delete/<id>`
     * Method - `DELETE`
     * Header - `Authorization <jwt token without signature>` (`user` key is mandatory in jwt payload data with valid email address which is used for storing/sending reminder email)
     * Example CURL - `curl --location --request DELETE 'http://127.0.0.1:678/reminders/delete/8' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJ1c2VyIjoicHJhc2FubmFzY29ycGlhbkBnbWFpbC5jb20ifQ.8eG-dXsnzaGf0t57tpu2mcuvW4asOVa9470KNynIG4U'`
   * Fetch Reminder:
     * URL - `http://127.0.0.1:678/reminders?status=all&per_page=10&page=2`
     * Method - `GET`
     * Header - `Authorization <jwt token without signature>` (`user` key is mandatory in jwt payload data with valid email address which is used for storing/sending reminder email)
     * Example CURL - `curl --location --request GET 'http://127.0.0.1:678/reminders?status=all&per_page=10&page=2' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJ1c2VyIjoicHJhc2FubmFzY29ycGlhbkBnbWFpbC5jb20ifQ.8eG-dXsnzaGf0t57tpu2mcuvW4asOVa9470KNynIG4U' \
--data '{
    "reminder_data":"Buy groceries on 20 April 2024"
}'`
     * Note: By default if page, per_page, status not mentioned then the API will fetch the response with fallback value as page=1, per_page=10, status=all
     * Reminder status can be: created, deleted, triggered, sent

## Features Covered
1. CORS enabled for all APIs.
2. Created Test cases for create, delete, fetch endpoints under `tests/` folder.
3. Oninit project startup `create_table()` is called to create `reminders` table if not present in MySQL database.
4. `env` are stored in `config` file.
5. Redis used for caching fetch endpoint. Caching is valid for `60` seconds.
6. `dateutil` python package is used for parsing date while creating a reminder. This package will handled most of case.
7. User validation done for `delete` and `fetch` endpoints.
8. RQ is used for queue management. In short words, instead of cron a job is invoked every 10s and will check for remainder. If found then the event it is published to `redis`. A thread is running for `redis subscribe` which will trigger the email using AWS SES.