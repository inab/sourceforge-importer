# SourceForge recipes importer 

This program extracts Bioinformatics software metadata from SourceForge and store it either in a JSON file or pushed to a MongoDB database.

## Set-up and Usage

### Option 1 (RECOMENDED) - Docker container 
The easiest way to run this importer is by using a docker image.
1. Pull the image 

    ```sh
    docker login registry.gitlab.bsc.es
    docker pull registry.gitlab.bsc.es/inb/elixir/software-observatory/sourceforge-importer
    ```

2. Run the container. 
If the ENV variables are stored in an `.env` file: 
    ```sh
    docker run --name [container-name] --env-file registry.gitlab.bsc.es/inb/elixir/software-observatory/sourceforge-importer
    ```

> :bulb: **Using `linux/amd64` architecture to run (and build) the container** 
>
>```sh
>export DOCKER_DEFAULT_PLATFORM=linux/amd64 
>```
> Necessary to run this container in a MacBook with M1 chip.


> :bulb: **Connecting to services in host** 
>
> Use `host.docker.internal` instead of `localhost` in the container to reach local services. For instance, to connect to a local MongoDB, use the string `host.docker.internal:27017`. 


### Option 2 - Native 

1. Clone this repository.

2. Install Python packages listed in `requirements.txt`.

    ```sh
    pip install -r requirements.txt
    ```

3. Execute the importer

    ```sh
    python3 main.py
    ``` 

> This program has been successfully executed using Python 3.8 and 3.9.


## Configuration

### Environment variables 

| Name             | Description | Default | Notes |
|------------------|-------------|---------|-------|
| STORAGE_MODE     |  Specifies whether the output will be stored in filesystem (`filesystem`) or pushed to a database (`db`) |  `db` |            |
| HOST       |  Host of database where output will be pushed |   `localhost`        |  Only used when STORAGE_MODE is `db`      |
| PORT       |  Port of database where output will be pushed |   `27017`            |  Only used when STORAGE_MODE is `db`      |
| DB         |  Name of database where output will be pushed |   `observatory`      |  Only used when STORAGE_MODE is `db`      |
| ALAMBIQUE |  Name of database where output will be pushed  |   `alambique`        |  Only used when STORAGE_MODE is `db`      |
| OUTPUT_PATH      |  Path to output file                    | `./data/bioconda.json` |  Only used when STORAGE_MODE is `filesystem` | 
| URL_SOURCEFORGE_PACKAGES | URL to SourceForge packages of our interest | `https://sourceforge.net/directory/science-engineering/bioinformatics/` | |