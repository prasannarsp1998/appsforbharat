#!/bin/sh
sleep 20s
export REDIS_URL=redis://redis:6379/0
rq worker --with-scheduler &
python app.py