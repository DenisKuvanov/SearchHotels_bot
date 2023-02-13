import redis


user_state_db = redis.StrictRedis(
    host='localhost',
    port=6379,
    db=0,
    charset='utf-8',
    decode_responses=True
)

user_history_db = redis.StrictRedis(
    host='localhost',
    port=6379,
    db=1,
    charset='utf-8',
    decode_responses=True
)