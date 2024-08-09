from redis import Redis
from rq import SimpleWorker

from transcription_service import config
from transcription_service.logger import log
from transcription_service.transcription import init_whisper_model


def main():
    log.info("Starting worker. Establishing connection to Redis...")
    redis_conn = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)

    log.info("Connection established. Preloading Whisper model...")
    # Preload the model to avoid loading it on each job execution – done in a specific (rather hacky/ugly) way because
    # of how redis queue and its workers are operating underneath. Some more information can be found
    # here: https://github.com/rq/rq/issues/1088 and https://python-rq.org/docs/workers/#performance-notes
    # TODO: potentially it can be embedded into the worker image itself, to trade off the startup time for the first job
    #       execution for storage space.
    init_whisper_model(config.WHISPER_MODEL_NAME, config.WHISPER_MODEL_DEVICE)

    log.info("Whisper model preloaded. Starting serving jobs...")
    worker = SimpleWorker(["default"], connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    main()
