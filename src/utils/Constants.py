TWITTER_BEARER_TOKEN_EVAR_KEY = 'TWITTER_BEARER_TOKEN'
TWITTER_BEARER_TOKEN_DEV_EVAR_KEY = 'TWITTER_BEARER_TOKEN_DEV'

OPENAI_API_KEY_EVAR_KEY = 'OPENAI_API_KEY'

RAW_TWEET_FILE_PREFIX = 'raw_'
SUM_TWEET_FILE_PREFIX = 'sum_'
INTRA_DAY_SUMMARY_FILE_PREFIX = 'agg_'
INTRA_DAY_SUMMARY_ENRICHED_FILE_PREFIX = 'enriched_'

MINIMAL_OPENAI_API_CALL_INTERVAL_SEC = 0.2
MIN_RAW_TWEET_LENGTH_FOR_EMBEDDING = 30
MAX_EMBEDDING_CACHE_SIZE = 5000

TWEET_LENGTH_CHAR_LIMIT = 280
TWEET_DEFAULT_POST_LIMIT = 4
TWEET_MATCH_SCORE_THRESHOLD = 0.9
TWEET_TOPIC_RELAVANCE_SCORE_THRESHOLD = 0.78

TWEET_VIDEO_DURATION_LIMIT_IN_SECOND_DEFAULT = 140  # 2 mins 20 secs

TWEET_SIMILARITY_FOR_POSTING_GUARD_THRESHOLD = 0.85
TWEET_SIMILARITY_FOR_REPLY = 0.8

TWITTER_ACCOUNT_FOLLOWER_COUNT_REACTION_THRESHOLD = 500000

TWEET_REPLY_MAX_AGE_SEC = 60 * 60 * 24  # 1 day
TWEET_THREAD_COVERAGE_SEC = 60 * 60 * 24 * 7  # 7 days

REDIS_TWEET_EMBEDDING_DICT_KEY = 'tweet_embedding_dict'
REDIS_SAVE_EMBEDDING_CACHE_INTERVAL_SEC = 60 * 5  # 5 mins

THREADS_SIMILARITY_CHECK_COVERAGE_IN_SEC = 60 * 60 * 24 * 3  # 3 days
THREADS_DEFAULT_POST_LIMIT = 5
THREADS_LENGTH_CHAR_LIMIT = 500
THREADS_SIMILARITY_FOR_POSTING_GUARD_THRESHOLD = 0.85
THREADS_SIMILARITY_FOR_REPLY = 0.8

PAST_DM_USER_IDS_REDIS_KEY_CRYPTO = 'past_dm_user_ids_crypto'
TODO_DM_USER_IDS_REDIS_KEY_CRYPTO = 'todo_dm_user_ids_crypto'
VISITED_INFLUENCER_ID_DICT_REDIS_KEY_CRYPTO = 'visited_influencer_id_dict_crypto'
DM_IG_ACCOUNTS = 'dm_ig_accounts'
DM_IG_ACCOUNT_INDEX = 'dm_ig_account_index'

INS_POST_INTERVAL_HOUR = 3