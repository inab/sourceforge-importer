# SourceForge recipes importer 

> ❗️⚙️ The data importation is run on a weekly basis using GitLab CI.

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
| HOST       |  Host of database where output will be pushed |   `localhost`        |  |
| PORT       |  Port of database where output will be pushed |   `27017`            |  |
| USER       |  User of database where output will be pushed |            |  |
| PASS   |  Password of database where output will be pushed |            |  |
| AUTH_SRC  |  Authentication source of database where output will be pushed |   `admin`  |  |
| DB         |  Name of database where output will be pushed |   `observatory`      |  |
| ALAMBIQUE |  Name of database where output will be pushed  |   `alambique`        |  |
| URL_OPEB_TOOLS | URL to OpenEBench Tools API | `https://openebench.bsc.es/monitor/tool` | |
| URL_SOURCEFORGE_PACKAGES | URL to SourceForge packages of our interest | `https://sourceforge.net/directory/bio-informatics/` | |

## CI/CD

This repository is integrated with GitLab CI/CD. The pipeline is defined in `.gitlab-ci.yml`. It is composed of the following stages:

| Stage | Description | Runs |
|-------|-------------|------|
| `dependencies` | Installs the dependencies | Always |
| `main_task` | Data importation | Manually or on schedule |
| `publish` | Builds and publishes the Docker image to the GitLab registry. The resulting image is tagged with the release tag | When a tag is created |

> :bulb: **Variables**
> The pipeline uses the variables `DOCKERHUB_USERNAME` and `DOCKERHUB_PASSWORD`. These variables are defined in the GitLab CI/CD settings.
