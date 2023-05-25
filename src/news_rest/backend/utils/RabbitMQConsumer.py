import pika

class RabbitMQConsumer:
    def __init__(self, host='localhost'):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host,virtual_host="/"))
        self.channel = self.connection.channel()
        self.channel.basic_qos(prefetch_count=10)

    def declare_queue(self, queue_name):
        # self.channel.queue_purge(queue_name)  # 清空指定队列的所有消息
        self.channel.queue_declare(queue=queue_name)

    def consume(self, queue_name, callback, auto_ack=True):
        self.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=auto_ack)
        self.channel.start_consuming()

    def close(self):
        self.connection.close()
