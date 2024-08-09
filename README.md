# Transcription service
This project extracts text transcriptions from movies and audio recordings in most popular video formats.


## Capabilities

- Supports transcription of both popular video and audio formats
- Should be able to handle long videos (up to several hours)
- Scalable architecture using Redis for job queuing
- Self-hosted solution using open-source Whisper AI model
- RESTful API for file upload and transcription status checking
- Separate worker processes for handling transcription tasks

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Poetry (Python package manager) (if not running with containers)

## Installation

### Clone this repository:
```bash
git clone <org_path>/transcription_service.git
cd transcription_service
```

### Create a virtual environment:
```bash
python<version> -m venv venv
```

### Activate the virtual environment:
```bash
source venv/bin/activate
```

### [Dev step only] Set up precommit
```bash
pre-commit insall
```

### [Deprecated/non-container only] Install dependencies using Poetry:
```bash
poetry install
```

## Usage

TODO: update/expand after the docker/compose is finalized

After installation, start the service using the following command:
```bash
uvicorn transcription_service.main:app --reload --env-file=.example.env
```
where:
- `--reload` flag enables auto-reloading of the server on code changes.
- `--env-file` flag specifies the path to the environment file – it can be omitted if variables are injected
into the environment using some other way.