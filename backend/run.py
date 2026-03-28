import threading
import webbrowser

import uvicorn

from app.utils.config import APP_HOST, APP_PORT, OPEN_BROWSER_ON_START

HOST = APP_HOST
PORT = APP_PORT
DOCS_URL = f"http://{HOST}:{PORT}/docs"


def open_browser() -> None:
    webbrowser.open(DOCS_URL)


if __name__ == "__main__":
    if OPEN_BROWSER_ON_START and HOST in {"127.0.0.1", "localhost"}:
        threading.Timer(1.0, open_browser).start()

    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)
