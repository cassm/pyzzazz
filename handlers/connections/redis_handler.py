import os

import redis


class RedisHandler:
    client = None

    @staticmethod
    def create_instance():
        RedisHandler.client = redis.StrictRedis(
            host=os.getenv("REDIS_IP"),
            port=os.getenv("REDIS_PORT"),
            db=0,
            decode_responses=True,
            password=os.getenv("REDIS_PW"))

    @staticmethod
    def get_instance():
        if not RedisHandler.client:
            RedisHandler.create_instance()

        return RedisHandler.client
