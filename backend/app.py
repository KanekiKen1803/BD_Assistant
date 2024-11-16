import json
from src import *
from flask import Flask, request

#Initiate Flask Server
app = Flask(__name__)

with open("config.json", "r") as fread:
    config = json.load(fread)


@app.route('/query', methods=["POST"])
def perform_query():
    return json.dumps(
        {
            "result": get_llm_response(config,request.get_json()["query"])
        }
    )

if __name__=="__main__":
    app.run(debug=True)