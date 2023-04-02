import pika

class RabbitMQConsumer:
    def __init__(self, queue_name, callback=None):
        self.observers = []
        self.queue_name = queue_name
        self.callback = callback

        # Connect to RabbitMQ server
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = self.connection.channel()

        # Declare queue
        self.channel.queue_declare(queue=self.queue_name)

        # Set up callback function to handle messages from the queue
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.handle_message, auto_ack=True)

    def add_observer(self, observer):
        self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)

    def handle_message(self, channel, method, properties, body):
        # This method should be overridden by child classes as needed
        pass

    def start_consuming(self):
        self.channel.start_consuming()
