import os
import sys

import pika

from send import email


def main():
    # RabbitMQ connection
    connection = pika.BlockingConnection(
        parameters=pika.ConnectionParameters(host="rabbitmq")  # our service name will resolve to the host IP for RabbitMQ service
    )
    channel = connection.channel()

    def callback(ch, method, properties, body):
        err = email.notify(body)
        if err:
            # send negative acknowledgment to the channel - we won't acknowledge that we've received and processed the message
            # => message won't be removed from the queue so that it can later be processed by another process
            ch.basic_nack(delivery_tag=method.delivery_tag)  # delivery tag uniquely identifies delivery on the channel
            # when we send that negative acknowledgment to the channel with the delivery tag RabbitMQ knows which message
            # hasn't been acknowledged so it will know not to remove that message from the queue
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get("MP3_QUEUE"),
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
