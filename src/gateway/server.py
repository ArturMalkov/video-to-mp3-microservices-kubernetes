import json
import os

import gridfs
import pika
from flask import Flask, request
from flask_pymongo import PyMongo

from auth import validate
from auth_svc import access
from storage import util


server = Flask(__name__)
server.config["MONGO_URI"] = "mongodb://host.minikube.internal:27017/videos"  # host.minikube.internal gives access to 'localhost' from within Kubernetes cluster

mongo = PyMongo(server)  # manages MongoDB connections for Flask app

fs = gridfs.GridFS(mongo.db)  # to store documents larger than 16 MB (default max BSON document size) (by sharding the file)

connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))  # to make communication with RabbitMQ synchronous
channel = connection.channel()


@server.route("/", methods=["POST"])
def login():
    """
    Communicates with auth service to log a user in and assign a JWT to that user.
    """
    jwt_token, err = access.login(request)

    if not err:
        return jwt_token

    return err


@server.route("/upload", methods=["POST"])
def upload():
    """
    Uploads a video to be converted to MP3.
    """
    # make sure a user has a JWT from /login
    access, err = validate.token(request)
    access = json.loads(access)

    if access["admin"]:  # i.e. if a user is authorized
        # make sure there's just one file to be uploaded
        if len(request.files) > 1 or len(request.files) < 1:
            return "exactly 1 file required", 400

        for _, file in request.files.items():
            err = util.upload(file, grid_fs, channel, access)

            if err:
                return err

        return "success!", 200

    return "not authorized", 401


@server.route("/download", methods=["GET"])
def download():
    """
    Downloads a MP3 file converted from a video.
    """

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
