import threading
import webbrowser

import uvicorn


HOST = "127.0.0.1"
PORT = 8000
DOCS_URL = f"http://{HOST}:{PORT}/docs"


def open_browser() -> None:
    webbrowser.open(DOCS_URL)


if __name__ == "__main__":
    threading.Timer(1.0, open_browser).start()
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)
