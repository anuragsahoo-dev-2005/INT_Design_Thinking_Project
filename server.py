import json
import logging
import sqlite3
from contextlib import closing
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "campusconnect.db"
MAX_BODY_SIZE = 1_000_000


def initialize_database():
    with closing(sqlite3.connect(DATABASE)) as connection:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS app_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )


class CampusConnectHandler(SimpleHTTPRequestHandler):
    def send_json(self, status, value):
        body = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/api/state":
            return super().do_GET()

        try:
            with closing(sqlite3.connect(DATABASE)) as connection:
                row = connection.execute(
                    "SELECT payload FROM app_state WHERE id = 1"
                ).fetchone()
        except sqlite3.Error:
            logging.exception("Could not read CampusConnect database")
            return self.send_json(500, {"error": "Could not read saved data."})

        state = json.loads(row[0]) if row else None
        self.send_json(200, {"state": state})

    def do_PUT(self):
        if self.path != "/api/state":
            return self.send_json(404, {"error": "Not found."})

        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.send_json(400, {"error": "Invalid Content-Length."})
        if size <= 0 or size > MAX_BODY_SIZE:
            return self.send_json(413, {"error": "Request body is empty or too large."})

        try:
            state = json.loads(self.rfile.read(size))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self.send_json(400, {"error": "Request body must be valid JSON."})

        if not isinstance(state, dict) or any(
            not isinstance(state.get(key), list)
            for key in ("faculty", "appts", "notifs")
        ):
            return self.send_json(
                400,
                {"error": "State must contain faculty, appts and notifs lists."},
            )

        payload = json.dumps(
            {key: state[key] for key in ("faculty", "appts", "notifs")},
            separators=(",", ":"),
        )
        try:
            with closing(sqlite3.connect(DATABASE)) as connection:
                with connection:
                    connection.execute(
                        """
                        INSERT INTO app_state (id, payload)
                        VALUES (1, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            payload = excluded.payload,
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        (payload,),
                    )
        except sqlite3.Error:
            logging.exception("Could not save CampusConnect data")
            return self.send_json(500, {"error": "Could not save data."})

        self.send_json(200, {"saved": True})


if __name__ == "__main__":
    initialize_database()
    server = ThreadingHTTPServer(("127.0.0.1", 8000), CampusConnectHandler)
    print("CampusConnect running at http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping CampusConnect.")
    finally:
        server.server_close()
