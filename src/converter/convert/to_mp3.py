import json
import os
import tempfile
from bson.objectid import ObjectId

import moviepy.editor
import pika


def start(message, fs_videos, fs_mp3s, channel):
    message = json.loads(message)

    # create empty temporary file to write video data to
    temporary_file = tempfile.NamedTemporaryFile()

    # get video file from MongoDB
    video_object_id = ObjectId(message["video_file_id"])  # convert video file id to ObjectId from a string
    video = fs_videos.get(video_object_id)

    # add video contents to empty file
    temporary_file.write(video.read())

    # create MP3 audio from temporary video file
    audio = moviepy.editor.VideoFileClip(temporary_file.name).audio

    temporary_file.close()  # temporary file will be deleted

    # write audio to the file
    temporary_file_path = tempfile.gettempdir() + f"/{message['video_file_id']}.mp3"
    audio.write_audiofile(temporary_file_path)

    # save file to MongoDB
    file = open(temporary_file_path, "rb")
    data = file.read()
    audio_file_id = fs_mp3s.put(data)
    file.close()
    os.remove(temporary_file_path)

    # update the received message
    message["mp3_file_id"] = str(audio_file_id)

    # put the message onto the queue
    try:
        channel.basic_publish(
            exchange="",
            routing_key=os.environ.get("MP3_QUEUE"),
            body=json.dumps(message),
            # make sure the message is persisted until it's processed
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )
    except Exception:
        fs_mp3s.delete(audio_file_id)
        return "failed to publish message"
