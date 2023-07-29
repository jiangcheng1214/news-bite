class NewsAPIItem:
    def __init__(self, initial_dict: dict):
        self.news_url = initial_dict.get("news_url")
        self.image_url = initial_dict.get("image_url")
        self.news_content = initial_dict.get("news_content")
        self.hashtags = initial_dict.get("hashtags")
        self.sentiment = initial_dict.get("sentiment")
        self.is_event = initial_dict.get("is_event")
        self.is_video = initial_dict.get("is_video")
        self.rank_score = initial_dict.get("rank_score")
