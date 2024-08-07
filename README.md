![](./.github/ren-light.png)

# Renderman has been retired as we are now able to render directly on GitHub Actions

Web server that hosts map tiles and renders changed tiles every hour (customisable)

## Docker Usage
1. Create a `.env` file:
    ```dotenv
    # Map data repo: https://github.com/<REPO_AUTHOR>/<REPO_NAME>
    REPO_AUTHOR=mrt-map
    REPO_NAME=map-data

    # GitHub token
    TOKEN=<token>
    # Optional, number of (Ray) processes that will be spawned
    PROCESSES=<int>
    ```

2. Pull the image with `docker pull ghcr.io/mrt-map/renderman:master`
3. Run the image with `docker run -dp <host_port>:8000 --env ./.env -v <host_vol_dir>:/vol ghcr.io/mrt-map/renderman:master`
   - `<host_port>` is the host's port
   - `<host_vol_dir>` is the volume directory that the image will mount onto
   - Optionally add `--shm-size=<size>` to give the renderer more shm
