import redis


class RedisHandler:
    client = None

    @staticmethod
    def create_instance():
        RedisHandler.client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

    @staticmethod
    def get_instance():
        if not RedisHandler.client:
            RedisHandler.create_instance()

        return RedisHandler.client
