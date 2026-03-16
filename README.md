# SourceForge recipes importer 

This program extracts Bioinformatics software metadata from SourceForge and push it to a MongoDB database.

## Set-up and Usage

1. Clone this repository.

2. Install Python packages listed in `requirements.txt`.

    ```sh
    pip install -r requirements.txt
    ```

3. Execute the importer

    ```sh
    python3 main.py -l=[log-level]
    ``` 
    - `log-level` is the level of logging. It can be `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`.

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

