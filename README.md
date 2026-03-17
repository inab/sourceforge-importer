# SourceForge recipes importer 

This program extracts Bioinformatics software metadata from SourceForge and push it to a MongoDB database.

## Set-up and Usage

1. Clone this repository.

2. Install Python packages listed in `requirements.txt`.

    ```sh
    pip install -r requirements.txt
    ```

3. Execute the importer.

    Start from scratch:

    ```sh
    python3 main.py -l INFO
    ```

    Resume from a previous run:

    ```sh
    python3 main.py --resume -l INFO
    ```

### Options

- `-l`, `--loglevel`: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`.
- `--resume`: resume from a previous checkpoint and reuse cached pages.
- `--max-requests`: maximum number of requests for the current run.
- `--min-delay`: minimum delay between successful requests.
- `--max-delay`: maximum delay between successful requests.
- `--max-consecutive-rate-limits`: stop after this many consecutive `429`, `403`, or `503` responses.

### Checkpoint and cache

- Processed projects are stored in `processed_sourceforge_projects.json`.
- Cached HTML pages are stored in `cache/sourceforge/`.

When the importer is run with `--resume`, it reuses both. Without `--resume`, it starts from zero and clears previous checkpoint and cache data.

### Why this importer works this way

SourceForge may return rate-limit or anti-bot responses after a high number of requests. To make long imports more robust, the importer:
- saves progress in a checkpoint file,
- caches downloaded HTML locally,
- limits the number of requests per run,
- and allows interrupted runs to be resumed safely.

> This program has been successfully executed using Python 3.8 and 3.9.


## Configuration

### Environment variables 

| Name             | Description | Default | Notes |
|------------------|-------------|---------|-------|
| MONGO_HOST       |  Host of database where output will be pushed |   `localhost`        |  |
| MONGO_PORT       |  Port of database where output will be pushed |   `27017`            |  |
| MONGO_USER       |  User of database where output will be pushed |            |  |
| MONGO_PASS   |  Password of database where output will be pushed |            |  |
| MONGO_AUTH_SRC  |  Authentication source of database where output will be pushed |   `admin`  |  |
| MONGO_DB         |  Name of database where output will be pushed |   `observatory`      |  |
| ALAMBIQUE |  Name of database where output will be pushed  |   `alambique`        |  |
| URL_OPEB_TOOLS | URL to OpenEBench Tools API | `https://openebench.bsc.es/monitor/tool` | |
| URL_SOURCEFORGE_PACKAGES | URL to SourceForge packages of our interest | `https://sourceforge.net/directory/bio-informatics/` | |

