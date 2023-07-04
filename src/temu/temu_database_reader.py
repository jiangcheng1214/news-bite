from logging import info
from utils.Utilities import get_clean_text
from typing import List
import mysql.connector
import clip
import torch
from twitter.TwitterAPIManager import TwitterAPIManager
from openAI.OpenaiClipFeatureGenerator import OpenaiClipFeatureGenerator


def all_quality_products():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345678",
            database="temu"
        )
        cursor = connection.cursor()
        sql = '''
SELECT 
    title, 
    seo_link_url, 
    thumb_url, 
    sold_quantity, 
    quantity, 
    json_extract(goods_comment, '$.comment_num') AS comment_num, 
    json_extract(goods_comment, '$.goods_score') AS goods_score,
    json_extract(price_info, '$.price') AS price,
    json_extract(price_info, '$.market_price') AS market_price,
    image_list
FROM
    products
where
	json_extract(price_info, '$.currency') = 'USD'
'''
    # and json_extract(price_info, '$.market_price') > 3000
    # and json_extract(goods_comment, '$.goods_score') > 4.5
    # and json_extract(goods_comment, '$.comment_num') > 2000
        cursor.execute(sql)
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(e)


device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load('ViT-B/32', device)


def embedding_of(text):
    clean_text = get_clean_text(text)
    text_input = clip.tokenize(clean_text).to(device)
    with torch.no_grad():
        text_features = model.encode_text(text_input)
    return text_features


def find_best_match_and_score(candidates: List, target: str, maapping_func=lambda x: x):
    candidate_text_list = [get_clean_text(
        maapping_func(candidate)) for candidate in candidates]
    with torch.no_grad():
        target_text_feature = embedding_of(target)
        candidate_text_features = [embedding_of(
            candidate_text) for candidate_text in candidate_text_list]
    similarity_scores = [torch.cosine_similarity(
        target_text_feature, candidate_text_feature).item() for candidate_text_feature in candidate_text_features]
    most_similar_index = similarity_scores.index(
        max(similarity_scores))
    most_similar_item = candidates[most_similar_index]
    return most_similar_item, similarity_scores[most_similar_index]


if __name__ == '__main__':
    # api_manager = TwitterAPIManager()
    # products_with_recommendation_reason = api_manager.generate_product_recommendation_for_user(
    #     '1194984822')
    # products = [x.split(' - ')[1].strip()
    #             for x in products_with_recommendation_reason]
    # temu_products = all_quality_products()
    # for product in products:
    #     best_match_product, best_score = find_best_match_and_score(
    #         temu_products, product, lambda x: x[0])
    #     info(
    #         f'Best match for {product} is {best_match_product} with score {best_score}')
