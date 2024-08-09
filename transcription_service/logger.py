import logging

from transcription_service import config

log = logging.getLogger()
log.setLevel(config.LOG_LEVEL)
if not log.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    formatter.default_time_format = "%Y-%m-%dT%H:%M:%S"
    formatter.default_msec_format = "%s.%03dZ"
    handler.setFormatter(formatter)
    log.addHandler(handler)

# Log object ready for import/usage
