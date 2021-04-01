"""
server.py
This script will launch a web server on port 8000 which sends SSE events anytime
logs are added to our log file.
"""

from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
from datetime import datetime
import uvicorn
from sh import tail
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
import time
import datetime
import os
import threading
import logging
import queue

#create our app instance
app = FastAPI()
q = queue.Queue()

real_path = os.path.realpath(__file__)
dir_path = os.path.dirname(real_path)
LOGFILE = f"{dir_path}/test.log"
app.mount("/client", StaticFiles(directory=f"{dir_path}/../client"), name="client")

#This async generator will listen to our log file in an infinite while loop (happens in the tail command)
#Anytime the generator detects a new line in the log file, it will yield it.
async def logGenerator(request):
    while True:
        if await request.is_disconnected():
            print("client disconnected!!!")
            break
        if not q.empty():
            line = q.get()
            yield line
        time.sleep(0.5)

#This is our api endpoint. When a client subscribes to this endpoint, they will recieve SSE from our log file
@app.get('/stream-logs')
async def runStatus(request: Request):
    event_generator = logGenerator(request)
    return EventSourceResponse(event_generator)

@app.get('/')
async def get_index():
    return FileResponse('client/client.html')

def worker():
    #infinite while loop printing to our log file.
    i = 0
    while True:
        d = datetime.datetime.now()
        q.put(f"{d} - log message num: {i}")
        i += 1
        time.sleep(0.3)

# start the background worker
t = threading.Thread(target=worker)
t.start()
t.join()
