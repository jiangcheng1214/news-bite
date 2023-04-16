import pika

class RabbitMQProducer:
    def __init__(self, host='localhost'):
        self.host = host

    def _connect(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
        self.channel = self.connection.channel()

    def _disconnect(self):
        self.connection.close()

    def declare_queue(self, queue_name):
        self._connect()
        self.channel.queue_declare(queue=queue_name)
        self._disconnect()

    def publish(self, queue_name, data):
        self._connect()
        self.channel.basic_publish(exchange='', routing_key=queue_name, body=data)
        print(f" [x] Sent data to queue {queue_name}")
        self._disconnect()