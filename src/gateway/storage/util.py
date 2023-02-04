import json

import pika


def upload(file, grid_fs, channel, access):
    """
    Uploads the file to MongoDB using grid_fs.
    Once the file has been successfully uploaded, a message is put onto RabbitMQ so that the downstream service can later
    process the upload by pulling it from MongoDB (asynchronous communication between the API gateway service and video
    processing service).
    """
    try:
        # save the video file to MongoDB
        file_id = grid_fs.put(file)
    except Exception:
        return "internal server error", 500

    # message to put onto the message queue
    message = {
        "video_file_id": str(file_id),  # since file_id is returned as ObjectID
        "mp3_file_id": None,
        "username": access["username"],
    }

    try:
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE  # to ensure messages are persisted on the queue in case of a pod crash/restart
            )
        )
    except Exception:
        # delete the corresponding file from MongoDB
        grid_fs.delete(file_id)
        return "internal server error", 500
