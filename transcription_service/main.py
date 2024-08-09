from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError
from rq import Queue

from transcription_service import config
from transcription_service.api import api_router


def _validate_redis_connection(redis_conn: Redis) -> bool:
    """
    Validate the Redis connection.
    :param redis_conn:
    :return: whether the connection is was successful and can be used
    """
    try:
        response = redis_conn.ping()
        if not response:
            return False
    except (RedisConnectionError, TimeoutError) as e:
        return False
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Run at startup
    Initialise the global objects and add them to app.state
    """
    config.UPLOADS_DIR.mkdir(exist_ok=True)
    config.TRANSCRIPTIONS_DIR.mkdir(exist_ok=True)

    app.state.redis_conn = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)
    redis_connection_successful = _validate_redis_connection(app.state.redis_conn)
    if not redis_connection_successful:
        raise ConnectionError("Startup failed. Could not connect to Redis.")
    app.state.queue = Queue(connection=app.state.redis_conn)
    yield
    """ 
    Run on shutdowns – close the connections, clear variables and release the resources.
    """


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
