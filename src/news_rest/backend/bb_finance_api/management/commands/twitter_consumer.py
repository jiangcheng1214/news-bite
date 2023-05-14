import json
from django.core.management.base import BaseCommand
from utils.RabbitMQConsumer import RabbitMQConsumer
from bb_finance_api.models import AuthorMetadata
from bb_finance_api.models import Tweet
class Command(BaseCommand):
    help = 'Consume Twitter data from RabbitMQ'
                        
    def handle(self, *args, **options):
        queue_name = 'twitter_messages'

        def callback(ch, method, properties, body):

            data = json.loads(body)

            # 提取tweet和author_metadata数据
            tweet_data = data['tweet']
            author_metadata_data = data['authorMetadata']

            # 检查AuthorMetadata是否已经存在，如果不存在则创建新记录
            author_metadata, created = AuthorMetadata.objects.get_or_create(
                id=author_metadata_data['id'],
                defaults={
                    'name': author_metadata_data['name'],
                    'username': author_metadata_data['username'],
                    'url': author_metadata_data['url'],
                    'description': author_metadata_data['description'],
                    'protected': author_metadata_data['protected'],
                    'verified': author_metadata_data['verified'],
                    'location': author_metadata_data['location'],
                    'created_at': author_metadata_data['created_at'],
                    'public_metrics': json.dumps(author_metadata_data['public_metrics']),
                }
            )

            # 创建新的Tweet记录并将其保存到数据库
            tweet = Tweet(
                author=author_metadata,
                created_at=tweet_data['created_at'],
                edit_history_tweet_ids=json.dumps(tweet_data['edit_history_tweet_ids']),
                entities=json.dumps(tweet_data['entities']),
                tweet_id=tweet_data['id'],
                lang=tweet_data['lang'],
                text=tweet_data['text']
            )
            tweet.save()

        rabbitmq_consumer = RabbitMQConsumer()
        rabbitmq_consumer.declare_queue(queue_name)
        rabbitmq_consumer.consume(queue_name, callback)


