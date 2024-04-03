from functools import wraps
from flask import request, abort
from flask import current_app
import os 
import json
import pandas as pd
import time

log_file = os.path.join(os.path.dirname(__file__), "../logs/api_request_call.json")
def log_api_request_call_middleware(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        start_time = time.perf_counter()
        start_time_2 = time.time()
        endpoint = request.endpoint.split('.')[-1]
        method = request.method
        url = request.url
        headers = dict(request.headers)
        timestamp = pd.Timestamp.now()
        print("this is between the start and end");
        response = f(*args, **kwargs)
        end_time = time.perf_counter()
        end_time_2 = time.time()
        elapsed_time = end_time - start_time
        elapsed_time_2 = end_time_2 - start_time_2
        # spent time in seconds
        spent_time = round(elapsed_time, 4)
        # spent time in miliseconds
        spent_time_2 = round(elapsed_time_2, 4)

        log = {
            "endpoint": endpoint,
            "method": method,
            "url": url,
            "headers": headers,
            "elapsed_time": spent_time,
            "elapsed_time_2": spent_time_2,
            "response": str(response),
            "timestamp": str(timestamp),
        }

        if os.path.exists(log_file):
            with open(log_file, "r") as logg:
                logs = json.load(logg)
            logs.append(log)
            with open(log_file, "w") as logg:
                json.dump(logs, logg)
        else:
            with open(log_file, "w") as logg:
                json.dump([log], logg)
        
        return f(*args, **kwargs)
        
    return decorated
