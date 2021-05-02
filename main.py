import renderer
import e
from threading import Thread
import flask
import json
import requests
import cloudinary.uploader
import cloudinary.api
import os
import io
import gc
import sys
import time
import psutil
from colorama import Fore, Style, init
init()

cloudinary.config( 
    cloud_name = "mrt-map", 
    api_key = "483664525357319", 
    api_secret = e.getenv("cloudinary")
)

def readFile(dir):
    with open(dir, "r") as f:
        data = json.load(f)
        f.close()
        return data

def writeFile(dir, value):
    with open(dir, "r+") as f:
        f.seek(0)
        f.truncate()
        json.dump(value, f, indent=0)
        f.close()

def splitList(l, g):
        r = []
        for i in range(g):
            r.append([])
        p = 0
        li = 0
        while p < len(l):
            r[li].append(l[p])
            li = 0 if li == len(r)-1 else li + 1
            p += 1
        return r

def render():
    if __name__ == '__main__':
        print("Loading pla")
        p = json.loads(requests.get("https://api.npoint.io/5fcc99fc5028693a9569").text)
        print("Loading nodes")
        n = json.loads(requests.get("https://api.npoint.io/0db5b7881915de645ced").text)
        print("Loading skin")
        s = renderer.misc.getSkin('default')

        gc.collect()
        tiles = renderer.render(p, n, s, 0, 8, 32*2**2, saveImages=False, processes=7)
        gc.collect()
        for tileName, tile in tiles.items():
            tileBytes = io.BytesIO()
            tile.save(tileBytes, format='PNG')
            tileBytes.name = tileName.replace(", ", "_")+".png"
            cloudinary.uploader.upload(tileBytes.getvalue(), public_id=tileName.replace(", ", "_"), overwrite=True, invalidate=True)
            print("Uploaded " + tileName)

if __name__ == '__main__':
    app = flask.Flask('')

    @app.route('/', methods=['GET'])
    def main():
        message = "je"
        return flask.render_template('index.html', message=message)

    @app.route('/render/', methods=['POST'])
    def render_post():
        render()
        return "Complete"

    #@app.route('/tilev/', methods=['GET'])
    #@flask_cors.cross_origin(origin='replit.com')
    #def tilev():
    #    try:
    #        v = readFile("index.json")[flask.request.args.get("t")]
    #        response = flask.jsonify({'some': 'data'})
    #        response.headers.add('Access-Control-Allow-Origin', '*')
    #        return response
    #        return str(v)
    #    except KeyError:
    #        flask.abort(404)

    def run():
        app.run(host="0.0.0.0", port=8080)
        #flask_cors.CORS(app)

    def clean():
        time.sleep(30)
        print(Fore.YELLOW)
        print("Before: " + str(gc.get_count()))
        gc.collect()
        print("After: " + str(gc.get_count()))
        process = psutil.Process(os.getpid())
        print(process.memory_info().rss/1000000)
        print(Style.RESET_ALL)
        time.sleep(30)

    server = Thread(target=run)
    server.start()
    #cleaner = Thread(target=clean)
    #cleaner.setDaemon(True)
    #cleaner.start()
    render()