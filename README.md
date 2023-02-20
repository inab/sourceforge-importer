# SourceForge recipes importer 

This program extracts Bioinformatics software metadata from SourceForge and store it either in a JSON file or pushed to a MongoDB database.

## Set-up and Usage

1. Clone this repository.

2. Install Python packages listed in `requirements.txt`.

    ```sh
    pip install -r requirements.txt
    ```

3. Execute the importer

    ```sh
    python3 main.py -l=[log-level] -d=[log-directory]
    ``` 
    - `log-level` is the level of logging. It can be `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`.
    - `log-directory` is the directory where the log file will be stored. If not specified, the log file will be stored in the current directory. 

> This program has been successfully executed using Python 3.8 and 3.9.


## Configuration

### Environment variables 

| Name             | Description | Default | Notes |
|------------------|-------------|---------|-------|
| STORAGE_MODE     |  Specifies whether the output will be stored in filesystem (`filesystem`) or pushed to a database (`db`) |  `db` |            |
| DBHOST       |  Host of database where output will be pushed |   `localhost`        |  Only used when STORAGE_MODE is `db`      |
| DBPORT       |  Port of database where output will be pushed |   `27017`            |  Only used when STORAGE_MODE is `db`      |
| DB         |  Name of database where output will be pushed |   `observatory`      |  Only used when STORAGE_MODE is `db`      |
| ALAMBIQUE |  Name of database where output will be pushed  |   `alambique`        |  Only used when STORAGE_MODE is `db`      |
| OUTPUT_PATH      |  Path to output file                    | `./data/bioconda.json` |  Only used when STORAGE_MODE is `filesystem` | 
| URL_SOURCEFORGE_PACKAGES | URL to SourceForge packages of our interest | `https://sourceforge.net/directory/science-engineering/bioinformatics/` | |