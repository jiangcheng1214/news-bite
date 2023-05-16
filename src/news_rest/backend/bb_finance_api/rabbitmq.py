from bb_finance_api.factory import RapidBBFinanceAPI
from bb_finance_models.models import BBFinanceStory
from rabbitmq import RabbitMQConsumer

class BBFinanceDetailRMQ(RabbitMQConsumer):
    def handle_message(self, channel, method, properties, body):
        # Convert the body to a string and retrieve the internal ID
        internal_id = body.decode()

        # Call the RapidBBFinanceAPI to retrieve the story details
        api = RapidBBFinanceAPI()
        story_data = api.get_story_detail(internal_id)

        # Create a new BBFinanceStory instance with the story data
        story = BBFinanceStory.from_dict(story_data)

        # Save the BBFinanceStory instance to the database
        story.save()

        # Notify the callback function if it exists
        if self.callback:
            self.callback(story)

        # Notify all observers
        for observer in self.observers:
            observer(story)
