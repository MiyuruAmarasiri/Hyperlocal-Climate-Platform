import pathlib
import sys
import time
from threading import Thread

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from flask import Flask  # noqa: E402
from dashboard.app import create_dash_app  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

def main():
    flask_server = Flask(__name__)
    dash_app = create_dash_app(server=flask_server)
    server = make_server('127.0.0.1', 8050, dash_app.server)
    thread = Thread(target=server.serve_forever)
    thread.start()
    time.sleep(3)
    server.shutdown()
    thread.join()

if __name__ == '__main__':
    main()
