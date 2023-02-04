import os
import sys

import gridfs  # to take video files from MongoDB and upload MP3 files to MongoDB
import pika
from pymongo import MongoClient

from convert import to_mp3


def main():
    client = MongoClient("host.minikube.internal", 27017)  # MongoDB is not deployed to our k8s cluster - it's run from localhost

    # MongoDB databases
    db_videos = client.videos  # 'video' database
    db_mp3s = client.mp3s  # 'mp3s' database

    # corresponding gridfs'
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    # RabbitMQ connection
    connection = pika.BlockConnection(
        parameters=pika.ConnectionParameters(host="rabbitmq")  # our service name will resolve to the host IP for RabbitMQ service
    )
    channel = connection.channel()

    def callback(ch, method, properties, body):
        err = to_mp3.start(body, fs_videos, fs_mp3s, ch)
        if err:
            # send negative acknowledgment to the channel - we won't acknowledge that we've received and processed the message
            # => message won't be removed from the queue so that it can later be processed by another process
            ch.basic_nack(delivery_tag=method.delivery_tag)  # delivery tag uniquely identifies delivery on the channel
            # when we send that negative acknowledgment to the channel with the delivery tag RabbitMQ knows which message
            # hasn't been acknowledged so it will know not to remove that message from the queue
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get("VIDEO_QUEUE"),
        on_message_callback=callback  # executed whenever a message is pulled from the queue
    )

    print("Waiting for messages. To exit press Ctrl+C")

    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        # gracefully shutting down the service in case of KeyboardInterrupt
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
