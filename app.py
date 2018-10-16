import os
from datetime import datetime
from elasticsearch import Elasticsearch
from flask import Flask, jsonify, request, Blueprint
from flasgger import Swagger



############################################################################
#                       Global configuration                               #
############################################################################
app = Flask(__name__)
api = Blueprint('api', __name__)
swagger_config = {
    "headers": [
    ],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_salud.json',
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flasgger_static_salud",
    # "static_folder": "static",  # must be set by user
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger = Swagger(app, config=swagger_config)
elastic_port = int(os.getenv('ELASTIC_PORT',9200))
elastic_ip = os.getenv('ELASTIC_IP','localhost')
elasticsearch_url = "{ip}:{port}"
es = Elasticsearch([elasticsearch_url.format(ip=elastic_ip, port=elastic_port)])
############################################################################
#                      Endpoint to save history                            #
############################################################################
@app.route("/<string:quiz_id>/<string:contact_urn>/", methods=['GET'])
def view_send_news(quiz_id, contact_urn):
    quiz_id = quiz_id.lower()
    if not es.indices.exists(index = quiz_id):
        es.indices.create(index = quiz_id)
    json_dict= {}
    for key in request.values:
        json_dict[key] = str(request.args.get(key))
    json_dict["CONTACT"] = contact_urn
    json_dict["CREATED_ON"] = datetime.now().strftime("%d-%m-%Y %H:%M")
    es.index(index = quiz_id,doc_type = contact_urn, body = json_dict)
    return jsonify({"ok": "ok"})

############################################################################
#                      Endpoint to show api history                        #
############################################################################
@app.route('/api/contact/<string:contact>/', methods=['GET'])
def get_history_contact(contact):
    """
    Display all quizes related with contact
    ---
    tags:
      - Contact
    parameters:
      - name: contact
        in: path
        type: string
        required: true
        description: Contact urn on rapidpro
    responses:
      500:
        description: Error not history found
      200:
        description: History of quizes
    """
    BODY = {
            "query": {
                "match": {
                    "CONTACT": contact
                }
            }
        }
    total_result = {}
    all_indexes = es.indices.get_alias("*")
    for index in all_indexes.keys():
        result = es.search(index = index, body = BODY)
        if result["hits"]["hits"]:
            total_result[index] = [item["_source"] for item in result["hits"]["hits"]]
    return jsonify(total_result)


@app.route('/api/quiz/<string:quiz>/', methods=['GET'])
def get_history_quiz(quiz):
    """
    Display all responses related with quiz
    ---
    tags:
      - Quiz
    parameters:
      - name: quiz
        in: path
        type: string
        required: true
        description: Contact urn on rapidpro
    responses:
      500:
        description: Error not history found
      200:
        description: History of quiz
    """
    total_result = {}
    try:
        result = es.search(index = quiz, body = {})
        if result["hits"]["hits"]:
            total_result[quiz] = [item["_source"] for item in result["hits"]["hits"]]
        return jsonify(total_result)
    except:
        return jsonify({"Historico no encontrado": "Not found"})



if __name__ == "__main__":
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(
        debug=True, host="0.0.0.0", port=int(os.getenv('WEBHOOK_PORT', 5000)))
