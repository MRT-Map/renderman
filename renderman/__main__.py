import logging
import os
import re
import subprocess
from datetime import datetime, timezone
from itertools import product
from multiprocessing import Process
from pathlib import Path
from time import sleep

import dill
import msgspec
import ray
import uvicorn
from fastapi import FastAPI, HTTPException
from renderer.misc_types.config import Config
from renderer.misc_types.coord import TileCoord, Vector

# noinspection PyProtectedMember
from renderer.misc_types.pla2 import Component, Pla2File, _enc_hook
from renderer.misc_types.zoom_params import ZoomParams
from renderer.render import MultiprocessConfig, render
from rich.logging import RichHandler
from rich.progress import track
from starlette.responses import Response

DOCKER = bool(os.getenv("DOCKER"))
TOKEN = os.getenv("TOKEN")
REPO_AUTHOR = os.getenv("REPO_AUTHOR")
REPO_NAME = os.getenv("REPO_NAME")

CWD = Path.cwd() / REPO_NAME
OLD_RENDERS_FILE = (Path("/vol") if DOCKER else Path.cwd()) / "old_renders.dill"
OLD_RENDERS_FILE.touch(exist_ok=True)

CONFIG = Config(
    zoom=ZoomParams(0, 9, 32),
    temp_dir=Path("../temp"),
)

logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    handlers=[RichHandler(markup=True, show_path=False)],
)

log = logging.getLogger("rich")

encoder = msgspec.json.Encoder(enc_hook=_enc_hook)


def eq(x: Component, y: Component) -> bool:
    return encoder.encode(x) == encoder.encode(y)


Component.__eq__ = eq


def init_repo() -> None:
    if CWD.exists():
        log.info("Pulling git repo")
        subprocess.run("git pull".split(), cwd=CWD).check_returncode()  # noqa: S603
    else:
        CWD.mkdir(exist_ok=True)
        log.info("Cloning git repo")
        if TOKEN:
            subprocess.run(
                f"git clone https://{TOKEN}@github.com/{REPO_AUTHOR}/{REPO_NAME} --depth 1".split()
            ).check_returncode()  # noqa: S603
        else:
            subprocess.run(
                f"git clone https://github.com/{REPO_AUTHOR}/{REPO_NAME} --depth 1".split()
            ).check_returncode()  # noqa: S603


def main() -> None:
    renders = []
    for file in track((CWD / "files").glob("*"), description="Loading components"):
        renders.extend(Pla2File.from_file(file).components)
    renders = list({(c.namespace, c.id): c for c in renders}.values())
    log.info("Total number of components: %s", len(renders))

    with OLD_RENDERS_FILE.open("rb+") as f:
        try:
            old_renders: list[Component] = dill.load(f)  # noqa: S301
        except EOFError:
            old_renders = renders
        dill.dump(renders, f)
    log.info("%s old components", len(old_renders))

    diffs = [
        a
        for a in track(old_renders, description="Finding changed components (1)")
        if a not in renders
    ] + [
        a
        for a in track(renders, description="Finding changed components (2)")
        if a not in old_renders
    ]
    log.info("Found %s changes", len(diffs))

    log.info("Finding tiles")
    old_tiles = set(Component.rendered_in(diffs, CONFIG.zoom))

    if len(old_tiles) == 0:
        log.info("No tiles to render")
        return

    tiles = old_tiles.copy()
    for ox, oy in track(
        product((-1, 0, 1), (-1, 0, 1)), description="Finding more tiles", total=9
    ):
        if ox == 0 and oy == 0:
            continue
        tiles = tiles.union({TileCoord(t.x + ox, t.y + oy, t.z) for t in tiles})

    renders = Pla2File(namespace="", components=renders)

    log.info("Starting render in %s tiles", len(tiles))
    render(
        renders,
        CONFIG,
        save_dir=CWD / "tiles",
        offset=Vector(0, 32),
        tiles=list(tiles),
        prepare_mp_config=MultiprocessConfig(serial=True),
    )
    ray.shutdown()

    for tile in track((CWD / "tiles").glob("*.webp"), description="Sorting tiles"):
        regex = re.search(r"[\\/](-?\d+), (-?\d+), (-?\d+)\.webp", str(tile))
        if regex is None:
            continue
        z, x, y = regex.group(1), regex.group(2), regex.group(3)

        new_path = CWD / Path(f"tiles/{z}/{x}/{y}.webp")
        new_dir = new_path.parent

        new_dir.mkdir(parents=True, exist_ok=True)
        new_path.unlink(missing_ok=True)
        tile.replace(new_path)

    subprocess.run("git add .".split(), cwd=CWD).check_returncode()  # noqa: S603
    message = f"Automatic render at {datetime.now(tz=timezone.utc)}"
    subprocess.run(
        [*f"git commit -am".split(), message], cwd=CWD
    ).check_returncode()  # noqa: S603
    subprocess.run("git push".split(), cwd=CWD).check_returncode()  # noqa: S603


def web():
    app = FastAPI()

    @app.get("/{z}/{x}/{y}.webp")
    def get_img(z: int, x: int, y: int) -> Response:
        path = CWD / Path(f"tiles/{z}/{x}/{y}.webp")
        if not path.exists():
            raise HTTPException(status_code=404)
        with path.open("rb") as f:
            b = f.read()
        return Response(content=b, media_type="image/webp")

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    init_repo()
    Process(target=web).start()
    while True:
        try:
            main()
        except Exception as e:
            log.exception(e.__traceback__)
        sleep(60 * 60)
        init_repo()
