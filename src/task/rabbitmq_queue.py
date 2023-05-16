import pika

# Set up a connection to the RabbitMQ server
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)

channel = connection.channel()

# Declare a queue
channel.queue_declare(queue='twitter_raw_data')

connection.close()
