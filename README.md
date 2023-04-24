# Renderman

Web server that hosts map tiles and renders changed tiles every hour (customisable)

## Docker Usage
1. Clone this repo and build this image (`docker build -t renderman .`)
2. Create an `.env` file:
    ```dotenv
    # Map data repo: https://github.com/<REPO_AUTHOR>/<REPO_NAME>
    REPO_AUTHOR=mrt-map
    REPO_NAME=map-data

    # GitHub token
    TOKEN=<token>
    ```
3. Run the image with `docker run -dp <host_port>:8000 --env ./.env -v <host_vol_dir>:/vol renderman`
   - `<host_port>` is the host's port
   - `<host_vol_dir>` is the volume directory that the image will mount onto
   - Optionally add `--shm-size=<size>` to give the renderer more shm