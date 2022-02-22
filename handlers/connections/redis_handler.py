import redis


class RedisHandler:
    client = None

    @staticmethod
    def create_instance():
        RedisHandler.client = redis.Redis(host='localhost', port=6379, db=0)

    @staticmethod
    def get_instance():
        if not RedisHandler.client:
            RedisHandler.create_instance()

        return RedisHandler.client