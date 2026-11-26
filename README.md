# INT_Design_Thinking_Project
# CampusConnect

CampusConnect is a university platform that helps students check faculty availability, view consultation hours, and book appointments for academic doubts. Faculty can manage schedules, update availability, and approve or reject requests.

## Run locally

1. Install Python 3.10 or later (no extra packages are needed).
2. From this folder, run `python server.py`.
3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000).
4. Sign in with one of the demo accounts shown on the login page.

The server creates `campusconnect.db` beside `server.py` on first run. Faculty availability, appointment requests, and notifications are stored in SQLite and shared by browsers using this local server. Existing browser demo data is used to initialize the database the first time it is opened.

This is a local class-project prototype: demo logins are not real authentication, and the server is intentionally bound to this computer rather than exposed to the internet.
