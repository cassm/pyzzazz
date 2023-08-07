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
            socket_timeout=15,
            socket_connect_timeout=15,
            decode_responses=True,

            password=os.getenv("REDIS_PW"))

    @staticmethod
    def get_instance():
        if not RedisHandler.client:
            RedisHandler.create_instance()

        return RedisHandler.client

    def try_command(f, *args, **kwargs):
        try:
            return f(*args, **kwargs)
        except redis.ConnectionError:
            return None

    @staticmethod
    def is_connected():
        try:
            RedisHandler.get_instance().ping()
            return True
        except redis.ConnectionError as e:
            print(e)
            return False
