from redis import Redis
from rq import Worker

from transcription_service import config


def main():
    redis_conn = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)
    redis_conn.ping()

    worker = Worker(["default"], connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    main()
