class InstagramPostCandidate:
    def __init__(self, initial_dict: dict):
        self.content_with_hashtags = initial_dict.get("content_with_hashtags")
        self.post_image_path = initial_dict.get("post_image_path")
        self.story_image_path = initial_dict.get("story_image_path")
        self.rank_score = initial_dict.get("rank_score")
        self.sentiment = initial_dict.get("sentiment")
        self.news_url = initial_dict.get("news_url")

    def __repr__(self):
        return {
            "content_with_hashtags": self.content_with_hashtags,
            "post_image_path": self.post_image_path,
            "story_image_path": self.story_image_path,
            "rank_score": self.rank_score,
            "sentiment": self.sentiment
        }
