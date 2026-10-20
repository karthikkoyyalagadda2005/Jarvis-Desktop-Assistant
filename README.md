Personal Assistant — React, Flask & MongoDB
A web-based personal assistant built with React for the user interface, Flask for the Python API, and MongoDB for command history. It accepts typed or spoken commands, performs supported local actions, looks up information on the web, and can read responses aloud using browser speech synthesis.
Project status: This README describes the implementation in the supplied project archive. Browser-only commands, backend commands, external search, and MongoDB history have different runtime requirements. See the setup and troubleshooting sections before running it.
Contents
    • Features
    • Technology stack
    • How it works
    • Project structure
    • Requirements
    • Installation
    • Configuration
    • Run the application
    • Usage and example commands
    • Backend API reference
    • Command history and database
    • Troubleshooting
    • Security notes
    • Development and next steps
Features
Interactive assistant dashboard
    • Dark, responsive interface with an assistant response panel.
    • Command input with Enter-to-submit support (Shift+Enter can be used for a newline).
    • Quick-action buttons for common tasks.
    • Recent command history panel with a refresh action.
    • Loading/processing state and visible error messages.
Voice interaction
    • Speech recognition: uses the browser's SpeechRecognition or webkitSpeechRecognition API where supported.
    • Text-to-speech: reads assistant responses aloud with the browser's speechSynthesis API.
    • Repeat and stop controls for spoken responses.
    • Voice recognition is browser-dependent and may require microphone permission. Chrome-based browsers are generally the best starting point.
Local commands
The Python assistant core recognizes commands for:
    • Current time and date.
    • Opening the home, Downloads, Documents, and Pictures folders.
    • Opening a terminal, if a supported terminal application is installed.
Local folder and terminal actions run on the machine running the Flask backend, not on the computer hosting the browser. These commands are most appropriate when frontend and backend run on the same personal computer.
Information lookup
    • Wikipedia topic lookup.
    • Google web search with content extraction.
    • A smart-search flow that attempts an information lookup and uses web search as a fallback.
    • Configurable timeouts and result/summary limits through environment variables.
External lookup depends on internet access and the availability/behavior of third-party websites and search services. It is not an LLM-based conversational model; results are based on lookup and extraction logic implemented in the backend.
Command history
    • Stores command text, response text, response type, and UTC creation timestamp in MongoDB.
    • Returns the latest records first.
    • Keeps the assistant usable for many commands even if database initialization fails, although history endpoints will not be available.
Technology stack
Layer	Technologies
Frontend	React, React DOM, JavaScript, Vite
UI	CSS, responsive layout
Backend	Python, Flask, Flask-CORS
Database	MongoDB, PyMongo
Web lookup	Requests, Beautiful Soup, googlesearch package and backend lookup logic
Voice	Browser Web Speech APIs

How it works
User
  |
  v
React UI (Vite development server)
  |-- Browser-only shortcuts: Google / YouTube
  |-- Browser speech recognition and speech synthesis
  |
  | HTTP requests (JSON)
  v
Flask API (default: 127.0.0.1:5000)
  |-- Local command router (assistant_core.py)
  |-- Wikipedia / web-search helpers (app.py)
  |-- Command history service (db.py)
  |
  v
MongoDB (default URI: mongodb://localhost:27017)
Typical command lifecycle:
    1. The user types a command or speaks it into the browser.
    2. React sends most commands to POST /command.
    3. Flask checks whether the local assistant core can handle the command.
    4. If it is not a local command, the backend's smart-search flow handles the query.
    5. The backend returns a JSON response.
    6. React displays the response and asks the browser to speak it, if speech synthesis is supported.
    7. The backend attempts to save the command and response to MongoDB.
    8. React reloads GET /history to refresh the activity panel.
Special case: “open Google” and “open YouTube” are handled directly in the browser by the frontend. They do not use the backend command route in the current implementation.
Project structure
React_Python_Flask/
├── backend/
│   ├── app.py                 # Flask app, routes, web lookup, command orchestration
│   ├── assistant_core.py      # Local command routing and OS-level actions
│   ├── db.py                  # MongoDB connection and history persistence
│   ├── .env                   # Local configuration; do not commit this file
│   └── requirements.txt        # Create this file using the dependency list below
└── frontend/
    ├── index.html
    ├── package.json           # Frontend dependencies and npm scripts
    ├── vite.config.js
    ├── src/
    │   ├── App.jsx            # Main dashboard and frontend behavior
    │   ├── App.css            # Dashboard styles
    │   ├── index.css           # Base styles (review for conflicting starter styles)
    │   └── main.jsx           # React entry point
    └── public/                # Static assets
The archive includes generated/dependency directories. They are not source code and should not be committed to version control: frontend/node_modules/, Python __pycache__/, and editor swap files. Install dependencies from the manifests instead.
Requirements
    • Python 3.10 or newer is recommended.
    • Node.js compatible with the Vite version in frontend/package.json (use a current supported Node.js LTS release).
    • npm.
    • MongoDB Community Server or a MongoDB container.
    • Internet access for Wikipedia and web search.
    • A modern browser. Microphone access requires browser support and permission.
Check installed tools:
python3 --version
node --version
npm --version
Installation
Run these commands from the project root.
1. Get the project
Extract the supplied archive, then enter the project directory:
unzip React_Python_Flask.zip
cd React_Python_Flask
If you have already extracted it, simply cd into the resulting directory.
2. Set up the Python backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
Install the packages used by the backend:
python -m pip install Flask flask-cors python-dotenv pymongo requests beautifulsoup4 googlesearch-python
Create a reproducible dependency file after confirming the environment works:
python -m pip freeze > requirements.txt
Then, on future installations, dependencies can be restored with:
python -m pip install -r requirements.txt
The project imports googlesearch from the googlesearch-python distribution. Avoid installing similarly named packages accidentally. If the external search library changes behavior or is rate-limited, web-search commands may need adjustment.
3. Start MongoDB
Use an existing local MongoDB service, or start a container if Docker/Podman is installed.
Example with Podman:
podman volume create mongodb_data
podman run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  docker.io/library/mongo:8
Check that the container is running:
podman ps
If a container named mongodb already exists, start it instead of creating another one:
podman start mongodb
For Docker, replace podman with docker. This example exposes MongoDB on the local machine without authentication; use it only for local development. Do not expose an unauthenticated database to an untrusted network.
4. Configure environment variables
The backend loads configuration from backend/.env. Keep real local values in that file and do not commit it. A starting template is:
ASSISTANT_NAME=Assistant
FRONTEND_URL=http://localhost:5173

MONGO_URI=mongodb://localhost:27017
MONGO_DATABASE=personal_assistant
MONGO_COLLECTION=command_history

SEARCH_TIMEOUT=10
WIKIPEDIA_TIMEOUT=8
GOOGLE_RESULT_LIMIT=5
WIKIPEDIA_RESULT_LIMIT=5
MAX_SUMMARY_LENGTH=1200

SEARCH_USER_AGENT=PersonalAssistant/1.0 (local development)
Adjust values to your environment. The database code defaults to mongodb://localhost:27017, database personal_assistant, and collection command_history when variables are absent.
Important: FRONTEND_URL configures allowed CORS origins. The current React app uses http://127.0.0.1:5000 as its API base URL, so run the backend on that address/port or update the frontend configuration if you deploy elsewhere. The Flask app's CORS configuration currently allows the default Vite origins listed in app.py.
5. Install frontend dependencies
Open a second terminal and return to the project root:
cd React_Python_Flask/frontend
npm install
Do not copy node_modules between machines or operating systems. npm install (or npm ci when a lockfile is committed) should install dependencies for the current environment.
Run the application
You need the database, backend, and frontend running.
Terminal 1 — MongoDB
If using the example container:
podman start mongodb
If it is already running, no action is needed.
Terminal 2 — Flask backend
cd React_Python_Flask/backend
source .venv/bin/activate
python app.py
The backend's routes are configured for port 5000 in the frontend. Confirm the health endpoint responds:
curl http://127.0.0.1:5000/
Expected response resembles:
{
  "success": true,
  "message": "Personal Assistant API is running."
}
If python app.py does not start the server, inspect the bottom of backend/app.py for its run configuration. If needed, run it using Flask's CLI from the backend directory:
flask --app app run --host 127.0.0.1 --port 5000
Terminal 3 — React frontend
cd React_Python_Flask/frontend
npm run dev
Open the local URL printed by Vite, typically:
    • http://localhost:5173
Keep all required terminals running while using the application.
Production build preview
From frontend/:
npm run build
npm run preview
The preview server serves the built frontend, but the Flask API must still be running and configured for the frontend's API URL. The current hard-coded localhost API URL is suitable for local development, not a production deployment.
Usage and example commands
Type a command in the input area, press Send, or use a quick-action button. You can also click the microphone button if the browser supports speech recognition.
Example command	Expected behavior
what time is it	Returns the current system time from the backend
what is today's date	Returns the current system date from the backend
open home folder	Opens the backend machine's home folder
open downloads	Opens the backend machine's Downloads folder
open documents	Opens the backend machine's Documents folder
open pictures	Opens the backend machine's Pictures folder
open terminal	Attempts to open an installed terminal application
open google	Opens Google in a new browser tab
open youtube	Opens YouTube in a new browser tab
wikipedia Python	Requests a Wikipedia lookup
search google for Flask REST API	Requests web search through the backend
who is the Prime Minister of India	Sends the question to the smart-search logic

The precise phrasing recognized by the local command router is defined in backend/assistant_core.py. Search routing and result formatting are implemented in backend/app.py.
Backend API reference
Base URL for local development: http://127.0.0.1:5000
GET /
Health check. Returns a JSON message indicating the API is running.
GET /time
Returns the current time from the backend system.
Example:
curl http://127.0.0.1:5000/time
GET /date
Returns the current date from the backend system.
GET /wiki?topic=<topic>
Looks up a Wikipedia topic.
Example:
curl --get \
  --data-urlencode "topic=Python programming language" \
  http://127.0.0.1:5000/wiki
A topic is required. An empty topic returns HTTP 400.
GET /search?q=<query>
Runs a web search for the supplied query.
Example:
curl --get \
  --data-urlencode "q=Flask Python framework" \
  http://127.0.0.1:5000/search
A query is required. An empty query returns HTTP 400.
POST /command
Main command endpoint. Send JSON with a command string.
Example:
curl -X POST http://127.0.0.1:5000/command \
  -H "Content-Type: application/json" \
  -d '{"command":"what time is it"}'
A successful response generally contains fields such as success, type, and response. Search-related responses may include additional metadata.
POST /open-folder
Requests a supported folder action through the backend. The endpoint validates folder names against an allowlist.
Example:
curl -X POST http://127.0.0.1:5000/open-folder \
  -H "Content-Type: application/json" \
  -d '{"folder":"downloads"}'
Supported folder names are defined in backend/app.py.
GET /history
Returns recent command history from MongoDB. If the database is unavailable, the endpoint returns a service-unavailable response and an empty history payload.
Command history and database
The Database class in backend/db.py manages MongoDB access.
Each stored record contains:
    • command_text — the submitted command.
    • response_text — the assistant's response.
    • response_type — a category where supplied by the caller.
    • created_at — a UTC timestamp.
The collection is sorted by created_at in descending order, and the current implementation limits history retrieval to the latest 100 records by default.
The backend intentionally catches database errors in several places. That allows some command handling to continue without MongoDB, but command history will be unavailable until the connection is restored.
Troubleshooting
Frontend cannot connect to Flask
    • Start the backend and verify curl http://127.0.0.1:5000/.
    • Confirm API_BASE_URL in frontend/src/App.jsx matches the backend address.
    • Check the browser console and Flask terminal for errors.
    • Ensure CORS allows the frontend origin.
ModuleNotFoundError in Python
Activate the backend virtual environment and install the dependencies listed in the installation section. Verify the correct interpreter is active with which python.
MongoDB connection fails
    • Confirm MongoDB is running and port 27017 is available.
    • Check MONGO_URI in backend/.env.
    • Check container status with podman ps or docker ps.
    • The assistant may still handle some commands, but /history requires a working database.
Vite or native dependency errors
From frontend/, try a clean dependency install:
rm -rf node_modules
npm install
npm run dev
Use a supported Node.js version for the Vite version in package.json. Do not delete your lockfile unless you intend to regenerate dependency versions.
Microphone button does not work
    • Use a browser that supports SpeechRecognition/webkitSpeechRecognition.
    • Allow microphone permission for the local site.
    • Check that the microphone is available and not being used exclusively by another application.
    • If voice recognition is unsupported, use typed commands. Text-to-speech support is separate from speech recognition.
The assistant says it cannot open a folder or terminal
Those actions run on the backend host. Check that the folder exists and that the operating system has a supported file manager or terminal installed. In a remote server/container deployment, opening a folder will affect the server environment, not the browser user's computer.
Search results are empty or inconsistent
External search providers may rate-limit automated requests, change HTML, or block scraping. Check internet connectivity and backend logs. Use the direct /wiki or /search endpoints to isolate the failing component.
Security notes
    • Never commit .env files, credentials, tokens, or private connection strings. Provide a sanitized .env.example instead.
    • The project archive should not include .env, node_modules, __pycache__, or editor swap files when shared publicly.
    • Do not expose the Flask development server or an unauthenticated MongoDB instance directly to the public internet.
    • The current frontend has a hard-coded localhost API URL; configure a proper environment-based API URL before deployment.
    • Add authentication, authorization, request validation, rate limiting, and production logging before exposing the API to other users.
    • Web content returned by external sites should be treated as untrusted input.
    • Commands that open local folders or terminals have operating-system side effects. Review and restrict command behavior before running the backend on a shared or production machine.
    • This project is a personal-assistant prototype and should not be considered production-hardened without further testing.
Development and next steps
Useful improvements to consider:
    1. Move the frontend API URL into a Vite environment variable such as VITE_API_BASE_URL.
    2. Add backend/requirements.txt and commit a frontend lockfile for repeatable installations.
    3. Add .gitignore rules for .env, .venv/, __pycache__/, node_modules/, and editor swap files.
    4. Add automated tests for command routing, API responses, database failure behavior, and search parsing.
    5. Add a dedicated /health endpoint that reports API and database status separately.
    6. Improve search resilience with retries, clearer source links, and robust parsing.
    7. Add a configurable voice language and user-selectable speech voice.
    8. Add authentication and authorization before allowing remote access.
    9. Consider a proper deployment setup using a production WSGI server and a reverse proxy.
    10. Review frontend/src/index.css and frontend/src/App.css together to ensure starter styles do not conflict with the dashboard styles.
License
No license is specified in the supplied project files. Add a LICENSE file before distributing the project if you want to grant others explicit reuse rights.
