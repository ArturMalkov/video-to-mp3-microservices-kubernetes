import json

import gridfs
import pika
from bson.objectid import ObjectId
from flask import Flask, request, send_file
from flask_pymongo import PyMongo

from auth import validate
from auth_svc import access
from storage import util


server = Flask(__name__)
# server.config["MONGO_URI"] = "mongodb://host.minikube.internal:27017/videos"  # host.minikube.internal gives access to 'localhost' from within Kubernetes cluster

# mongo = PyMongo(server)  # manages MongoDB connections for Flask app

mongo_video = PyMongo(server, uri="mongodb://host.minikube.internal:27017/videos")
mongo_mp3 = PyMongo(server, uri="mongodb://host.minikube.internal:27017/mp3s")

# fs = gridfs.GridFS(mongo.db)  # to store documents larger than 16 MB (default max BSON document size) (by sharding the file)
fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))  # to make communication with RabbitMQ synchronous
channel = connection.channel()


@server.route("/login", methods=["POST"])
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

    if err:
        return err

    access = json.loads(access)

    if access["admin"]:  # i.e. if a user is authorized
        # make sure there's just one file to be uploaded
        if len(request.files) > 1 or len(request.files) < 1:
            return "exactly 1 file required", 400

        for _, file in request.files.items():
            err = util.upload(file, fs_videos, channel, access)

            if err:
                return err

        return "success!", 200

    return "not authorized", 401


@server.route("/download", methods=["GET"])
def download():
    """
    Downloads a MP3 file converted from a video.
    """
    access, err = validate.token(request)

    if err:
        return err

    access = json.loads(access)

    if access["admin"]:
        file_id_string = request.args.get("file_id")

        if not file_id_string:
            return "file_id is required", 400

        try:
            mp3_file = fs_mp3s.get(ObjectId(file_id_string))
            return send_file(mp3_file, download_name=f"{file_id_string}.mp3")  # this will be able to determine the MIME type of the file
        except Exception as err:
            print(err)
            return "internal server error", 500

    return "not authorized", 401


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
