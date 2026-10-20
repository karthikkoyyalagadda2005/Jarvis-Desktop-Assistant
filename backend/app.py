
#wikipedia and google search are handled in assistant_core.py, so app.py should not handle them.


import os
import re
import time
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from googlesearch import search

from assistant_core import PersonalAssistant
from db import Database


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# CORS
# ============================================================

frontend_url = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
)

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                frontend_url,
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]
        }
    },
)


# ============================================================
# PERSONAL ASSISTANT
# ============================================================

assistant = PersonalAssistant(
    name=os.getenv(
        "ASSISTANT_NAME",
        "Assistant",
    )
)


# ============================================================
# DATABASE
# ============================================================

database = None

try:

    database = Database()

    if database.test_connection():

        print(
            "MongoDB connected successfully."
        )

    else:

        print(
            "MongoDB connection failed."
        )

except Exception as error:

    database = None

    print(
        f"Database initialization error: {error}"
    )


# ============================================================
# SEARCH CONFIGURATION
# ============================================================

SEARCH_TIMEOUT = int(
    os.getenv(
        "SEARCH_TIMEOUT",
        "10",
    )
)

WIKIPEDIA_TIMEOUT = int(
    os.getenv(
        "WIKIPEDIA_TIMEOUT",
        "8",
    )
)

GOOGLE_RESULT_LIMIT = int(
    os.getenv(
        "GOOGLE_RESULT_LIMIT",
        "5",
    )
)

WIKIPEDIA_RESULT_LIMIT = int(
    os.getenv(
        "WIKIPEDIA_RESULT_LIMIT",
        "5",
    )
)

MAX_SUMMARY_LENGTH = int(
    os.getenv(
        "MAX_SUMMARY_LENGTH",
        "1200",
    )
)


# ============================================================
# USER AGENT
# ============================================================

USER_AGENT = os.getenv(
    "SEARCH_USER_AGENT",
    (
        "PersonalAssistant/1.0 "
        "(https://localhost; "
        "contact@example.com)"
    ),
)


# ============================================================
# HTTP SESSION
# ============================================================

http = requests.Session()

http.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
    }
)


# ============================================================
# HELPER: CLEAN TEXT
# ============================================================

def clean_text(text):

    if text is None:
        return ""

    text = str(text)

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# HELPER: SAVE COMMAND
# ============================================================

def save_command(
    command_text,
    response_text,
):

    if database is None:
        return

    try:

        database.save_command(
            command_text=command_text,
            response_text=response_text,
        )

    except Exception as error:

        print(
            f"Database save error: {error}"
        )

# ============================================================
# HELPER: REMOVE SEARCH PREFIX
# ============================================================

def remove_search_prefix(command):

    command = clean_text(command)

    command_lower = command.lower()

    prefixes = [

        "search google for ",

        "search google ",

        "google search for ",

        "google search ",

        "search for ",

        "search ",

        "google ",

        "look up ",

        "find ",
    ]

    for prefix in prefixes:

        if command_lower.startswith(prefix):

            query = command[
                len(prefix):
            ].strip()

            if query:
                return query

    return command


# ============================================================
# HELPER:
# EXPLICIT GOOGLE REQUEST?
# ============================================================

def is_explicit_google_query(command):

    command_lower = clean_text(
        command
    ).lower()

    prefixes = [

        "search google ",

        "search google for ",

        "google search ",

        "google search for ",

        "google ",
    ]

    return any(
        command_lower.startswith(prefix)
        for prefix in prefixes
    )


# ============================================================
# HELPER:
# EXPLICIT WIKIPEDIA REQUEST?
# ============================================================

def is_explicit_wikipedia_query(command):

    command_lower = clean_text(
        command
    ).lower()

    prefixes = [

        "wikipedia ",

        "wiki ",

        "search wikipedia ",

        "search wikipedia for ",

        "wikipedia search ",

        "wikipedia search for ",

        "look up on wikipedia ",

        "look up in wikipedia ",
    ]

    return any(
        command_lower.startswith(prefix)
        for prefix in prefixes
    )


# ============================================================
# EXTRACT WIKIPEDIA QUERY
# ============================================================

def extract_wikipedia_query(command):

    command = clean_text(command)

    command_lower = command.lower()

    prefixes = [

        "search wikipedia for ",

        "search wikipedia ",

        "wikipedia search for ",

        "wikipedia search ",

        "look up on wikipedia ",

        "look up in wikipedia ",

        "wikipedia ",

        "wiki ",
    ]

    for prefix in prefixes:

        if command_lower.startswith(prefix):

            query = command[
                len(prefix):
            ].strip()

            if query:
                return query

    return command


# ============================================================
# CREATE WIKIPEDIA SEARCH QUERY
#
# This removes conversational words so that:
#
# "Who is the Prime Minister of India?"
#
# becomes approximately:
#
# "Prime Minister of India"
# ============================================================

def build_wikipedia_query(question):

    question = clean_text(question)

    query = question

    # Remove common question patterns.

    patterns = [

        r"^who is\s+",
        r"^who was\s+",
        r"^who are\s+",
        r"^what is\s+",
        r"^what was\s+",
        r"^what are\s+",
        r"^tell me about\s+",
        r"^can you tell me about\s+",
        r"^give me information about\s+",
        r"^information about\s+",
        r"^explain\s+",
        r"^describe\s+",
        r"^tell me\s+",
        r"^i want to know about\s+",
        r"^do you know about\s+",
        r"^can you explain\s+",
    ]

    for pattern in patterns:

        query = re.sub(
            pattern,
            "",
            query,
            flags=re.IGNORECASE,
        )

    # Remove question mark.

    query = query.rstrip("?!. ")

    return clean_text(query)


# ============================================================
# WIKIPEDIA SEARCH API
#
# Uses MediaWiki REST API directly.
#
# This is better than:
#
# wiki.page("who is prime minister...")
#
# because we first search for relevant pages.
# ============================================================

def wikipedia_search_pages(
    query,
    limit=5,
):

    query = clean_text(query)

    if not query:

        return []


    url = (
        "https://en.wikipedia.org/w/api.php"
    )

    params = {

        "action": "query",

        "list": "search",

        "srsearch": query,

        "format": "json",

        "utf8": 1,

        "srlimit": limit,

        "srprop": "snippet",
    }


    try:

        print(
            f"Wikipedia search query: {query}"
        )

        response = http.get(
            url,
            params=params,
            timeout=WIKIPEDIA_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        results = (
            data
            .get("query", {})
            .get("search", [])
        )

        return results

    except requests.Timeout:

        print(
            "Wikipedia search timeout."
        )

        return []

    except requests.RequestException as error:

        print(
            f"Wikipedia search request error: {error}"
        )

        return []

    except Exception as error:

        print(
            f"Wikipedia search error: {error}"
        )

        return []


# ============================================================
# GET WIKIPEDIA PAGE
# ============================================================

def wikipedia_get_page(
    title,
):

    title = clean_text(title)

    if not title:

        return None


    url = (
        "https://en.wikipedia.org/w/api.php"
    )

    params = {

        "action": "query",

        "prop": "extracts|info",

        "exintro": 1,

        "explaintext": 1,

        "inprop": "url",

        "redirects": 1,

        "titles": title,

        "format": "json",
    }


    try:

        print(
            f"Wikipedia page request: {title}"
        )

        response = http.get(
            url,
            params=params,
            timeout=WIKIPEDIA_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        pages = (
            data
            .get("query", {})
            .get("pages", {})
        )

        if not pages:

            return None

        page = next(
            iter(
                pages.values()
            )
        )

        if "-1" in page:

            return None

        return page

    except requests.Timeout:

        print(
            "Wikipedia page timeout."
        )

        return None

    except requests.RequestException as error:

        print(
            f"Wikipedia page request error: {error}"
        )

        return None

    except Exception as error:

        print(
            f"Wikipedia page error: {error}"
        )

        return None


# ============================================================
# SCORE WIKIPEDIA RESULT
# ============================================================

def score_wikipedia_result(
    question,
    result,
):

    question_words = set(
        re.findall(
            r"\b[a-zA-Z0-9]+\b",
            question.lower(),
        )
    )

    title = clean_text(
        result.get(
            "title",
            "",
        )
    )

    title_words = set(
        re.findall(
            r"\b[a-zA-Z0-9]+\b",
            title.lower(),
        )
    )

    if not question_words:
        return 0

    overlap = (
        question_words
        & title_words
    )

    score = len(overlap)

    return score


# ============================================================
# WIKIPEDIA LOOKUP
#
# Main intelligent Wikipedia function.
# ============================================================

def wikipedia_lookup(
    question,
):

    original_question = clean_text(
        question
    )

    if not original_question:

        return {
            "success": False,
            "response": (
                "Please provide a question."
            ),
            "title": "",
            "summary": "",
            "url": "",
            "source": "wikipedia",
        }


    # --------------------------------------------------------
    # Build better search query
    # --------------------------------------------------------

    search_query = build_wikipedia_query(
        original_question
    )

    print()
    print(
        "WIKIPEDIA LOOKUP"
    )
    print(
        f"Original: {original_question}"
    )
    print(
        f"Search query: {search_query}"
    )


    # --------------------------------------------------------
    # Search Wikipedia
    # --------------------------------------------------------

    results = wikipedia_search_pages(
        search_query,
        limit=WIKIPEDIA_RESULT_LIMIT,
    )


    if not results:

        return {
            "success": False,
            "response": (
                "Wikipedia did not return "
                "any relevant results."
            ),
            "title": "",
            "summary": "",
            "url": "",
            "source": "wikipedia",
        }


    # --------------------------------------------------------
    # Rank results
    # --------------------------------------------------------

    results = sorted(
        results,
        key=lambda item:
            score_wikipedia_result(
                original_question,
                item,
            ),
        reverse=True,
    )


    # --------------------------------------------------------
    # Try top results
    #
    # If first page has no useful extract,
    # try next related page.
    # --------------------------------------------------------

    for result in results:

        title = clean_text(
            result.get(
                "title",
                "",
            )
        )

        if not title:
            continue


        page = wikipedia_get_page(
            title
        )

        if not page:
            continue


        summary = clean_text(
            page.get(
                "extract",
                "",
            )
        )


        if not summary:
            continue


        # ----------------------------------------------------
        # Limit summary
        # ----------------------------------------------------

        if len(summary) > MAX_SUMMARY_LENGTH:

            summary = (
                summary[
                    :MAX_SUMMARY_LENGTH
                ]
                .rsplit(" ", 1)[0]
                + "..."
            )


        page_url = page.get(
            "fullurl",
            "",
        )


        response_text = (
            f"According to Wikipedia, "
            f"{summary}"
        )


        print(
            "Wikipedia answer found."
        )

        return {

            "success": True,

            "response": response_text,

            "title": page.get(
                "title",
                title,
            ),

            "summary": summary,

            "url": page_url,

            "source": "wikipedia",
        }


    # --------------------------------------------------------
    # Search results existed but no page content
    # --------------------------------------------------------

    return {

        "success": False,

        "response": (
            "Wikipedia found related pages, "
            "but I couldn't retrieve useful "
            "information from them."
        ),

        "title": "",

        "summary": "",

        "url": "",

        "source": "wikipedia",
    }


# ============================================================
# GOOGLE SEARCH
#
# Returns URLs.
# ============================================================

def google_search(
    query,
    limit=GOOGLE_RESULT_LIMIT,
):

    query = clean_text(query)

    if not query:

        return {

            "success": False,

            "response": (
                "Please provide a search query."
            ),

            "results": [],
        }


    try:

        print()
        print(
            "GOOGLE SEARCH"
        )

        print(
            f"Query: {query}"
        )


        results = []

        for url in search(
            query,
            num_results=limit,
            lang="en",
        ):

            url = clean_text(url)

            if not url:
                continue

            if url in results:
                continue

            results.append(url)

            if len(results) >= limit:
                break


        if not results:

            return {

                "success": False,

                "response": (
                    f"No Google results found "
                    f"for '{query}'."
                ),

                "results": [],
            }


        structured_results = []

        for url in results:

            structured_results.append({

                "title": "",

                "snippet": "",

                "url": url,

            })


        return {

            "success": True,

            "response": (
                f"I found {len(results)} "
                f"Google search results "
                f"for '{query}'."
            ),

            "results": structured_results,

        }


    except Exception as error:

        print(
            f"Google search error: {error}"
        )

        return {

            "success": False,

            "response": (
                "I couldn't perform the "
                "Google search right now."
            ),

            "results": [],
        }


# ============================================================
# FETCH WEB PAGE TEXT
#
# Used only as a fallback for Google results.
# ============================================================

def fetch_webpage_text(
    url,
    max_length=2000,
):

    if not url:
        return ""


    try:

        response = http.get(
            url,
            timeout=SEARCH_TIMEOUT,
            allow_redirects=True,
        )

        response.raise_for_status()


        content_type = (
            response.headers
            .get(
                "Content-Type",
                "",
            )
            .lower()
        )


        if (
            "text/html"
            not in content_type
        ):

            return ""


        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )


        # Remove unwanted elements.

        for element in soup(
            [
                "script",
                "style",
                "noscript",
                "nav",
                "footer",
                "header",
                "form",
            ]
        ):

            element.decompose()


        text = soup.get_text(
            " ",
            strip=True,
        )


        text = clean_text(text)


        if len(text) > max_length:

            text = (
                text[:max_length]
                .rsplit(" ", 1)[0]
                + "..."
            )


        return text


    except Exception as error:

        print(
            f"Webpage fetch error: "
            f"{type(error).__name__}: {error}"
        )

        return ""


# ============================================================
# GOOGLE SEARCH WITH CONTENT
#
# First gets Google URLs.
# Then tries to fetch useful page text.
# ============================================================

def google_search_with_content(
    query,
    limit=GOOGLE_RESULT_LIMIT,
):

    base_result = google_search(
        query,
        limit,
    )


    if not base_result["success"]:

        return base_result


    enriched_results = []


    for item in base_result["results"]:

        url = item["url"]

        page_text = fetch_webpage_text(
            url
        )


        enriched_results.append({

            "title": item.get(
                "title",
                "",
            ),

            "snippet": item.get(
                "snippet",
                "",
            ),

            "url": url,

            "content": page_text,

        })


    # --------------------------------------------------------
    # Create response
    # --------------------------------------------------------

    useful_content = None

    for item in enriched_results:

        if item.get("content"):

            useful_content = item
            break


    if useful_content:

        content = useful_content[
            "content"
        ]


        response_text = (
            f"According to a web result, "
            f"{content}"
        )


    else:

        response_text = (
            f"I found {len(enriched_results)} "
            f"Google results for '{query}'."
        )


    return {

        "success": True,

        "response": response_text,

        "results": enriched_results,

    }


# ============================================================
# SMART WEB SEARCH
#
# Order:
#
# Explicit Google request
#       ↓
# Google
#
# Explicit Wikipedia request
#       ↓
# Wikipedia
#       ↓
# Google fallback
#
# Normal question
#       ↓
# Wikipedia
#       ↓
# Google fallback
# ============================================================

def smart_search(
    question,
):

    question = clean_text(
        question
    )


    if not question:

        return {

            "success": False,

            "type": "error",

            "response": (
                "Please enter a question."
            ),

        }


    # ========================================================
    # EXPLICIT GOOGLE
    # ========================================================

    if is_explicit_google_query(
        question
    ):

        query = remove_search_prefix(
            question
        )

        google_result = (
            google_search_with_content(
                query
            )
        )

        google_result["type"] = "google"

        return google_result


    # ========================================================
    # EXPLICIT WIKIPEDIA
    # ========================================================

    if is_explicit_wikipedia_query(
        question
    ):

        query = extract_wikipedia_query(
            question
        )

        wiki_result = wikipedia_lookup(
            query
        )


        if wiki_result["success"]:

            wiki_result["type"] = (
                "wikipedia"
            )

            return wiki_result


        # Wikipedia failed.
        # Use Google fallback.

        print(
            "Wikipedia failed. "
            "Trying Google fallback."
        )


        google_result = (
            google_search_with_content(
                question
            )
        )

        google_result["type"] = (
            "google_fallback"
        )

        return google_result


    # ========================================================
    # NORMAL NATURAL-LANGUAGE QUESTION
    # ========================================================

    print(
        "Natural-language question detected."
    )


    # --------------------------------------------------------
    # FIRST: WIKIPEDIA
    # --------------------------------------------------------

    wiki_result = wikipedia_lookup(
        question
    )


    if wiki_result["success"]:

        wiki_result["type"] = (
            "wikipedia"
        )

        return wiki_result


    # --------------------------------------------------------
    # SECOND: GOOGLE
    # --------------------------------------------------------

    print(
        "Wikipedia did not provide "
        "a useful answer."
    )

    print(
        "Falling back to Google."
    )


    google_result = (
        google_search_with_content(
            question
        )
    )

    google_result["type"] = (
        "google"
    )

    return google_result


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return jsonify({

        "success": True,

        "message": (
            "Personal Assistant API "
            "is running."
        ),

    })


# ============================================================
# TIME
# ============================================================

@app.get("/time")
def get_time():

    try:

        response_text = (
            assistant.get_time()
        )

        return jsonify({

            "success": True,

            "response": response_text,

        })

    except Exception as error:

        print(
            f"Time error: {error}"
        )

        return jsonify({

            "success": False,

            "response": (
                "Unable to get "
                "the current time."
            ),

        }), 500


# ============================================================
# DATE
# ============================================================

@app.get("/date")
def get_date():

    try:

        response_text = (
            assistant.get_date()
        )

        return jsonify({

            "success": True,

            "response": response_text,

        })

    except Exception as error:

        print(
            f"Date error: {error}"
        )

        return jsonify({

            "success": False,

            "response": (
                "Unable to get "
                "today's date."
            ),

        }), 500


# ============================================================
# WIKIPEDIA API
#
# GET /wiki?topic=python
# ============================================================

@app.get("/wiki")
def wiki_api():

    topic = clean_text(
        request.args.get(
            "topic",
            "",
        )
    )


    if not topic:

        return jsonify({

            "success": False,

            "type": "wikipedia",

            "response": (
                "Please provide "
                "a Wikipedia topic."
            ),

            "title": "",

            "summary": "",

            "url": "",

        }), 400


    result = wikipedia_lookup(
        topic
    )


    result["type"] = "wikipedia"


    return jsonify(result)


# ============================================================
# GOOGLE API
#
# GET /search?q=python
# ============================================================

@app.get("/search")
def search_api():

    query = clean_text(
        request.args.get(
            "q",
            "",
        )
    )


    if not query:

        return jsonify({

            "success": False,

            "type": "google",

            "response": (
                "Please provide "
                "a search query."
            ),

            "results": [],

        }), 400


    result = google_search_with_content(
        query
    )


    result["type"] = "google"


    return jsonify(result)


# ============================================================
# OPEN FOLDER
# ============================================================

@app.post("/open-folder")
def open_folder_api():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    folder = clean_text(
        data.get(
            "folder",
            "",
        )
    ).lower()


    allowed_folders = {

        "home",

        "downloads",

        "documents",

        "pictures",

    }


    if folder not in allowed_folders:

        return jsonify({

            "success": False,

            "response": (
                "Invalid folder. "
                "Allowed folders are "
                "home, downloads, "
                "documents and pictures."
            ),

        }), 400


    try:

        response_text = (
            assistant.open_folder(
                folder
            )
        )


        save_command(
            f"open {folder}",
            response_text,
        )


        return jsonify({

            "success": True,

            "response": response_text,

        })


    except Exception as error:

        print(
            f"Open folder error: {error}"
        )


        return jsonify({

            "success": False,

            "response": (
                f"Unable to open "
                f"{folder}."
            ),

        }), 500


# ============================================================
# GENERIC COMMAND
#
# POST /command
#
# {
#   "command": "who is prime minister of india"
# }
# ============================================================

@app.post("/command")
def command_api():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    print()
    print("=" * 70)
    print(
        "PERSONAL ASSISTANT COMMAND"
    )
    print("=" * 70)


    command = clean_text(
        data.get(
            "command",
            "",
        )
    )


    print(
        f"User command: {command}"
    )


    if not command:

        return jsonify({

            "success": False,

            "type": "error",

            "response": (
                "Please enter a command."
            ),

        }), 400


    # ========================================================
    # 1. LOCAL COMMANDS
    # ========================================================

    try:

        core_response = (
            assistant.process_command(
                command
            )
        )

    except Exception as error:

        print(
            f"Core command error: {error}"
        )

        core_response = None


    if core_response is not None:

        save_command(
            command,
            core_response,
        )


        return jsonify({

            "success": True,

            "type": "command",

            "response": core_response,

        })


    # ========================================================
    # 2. SMART WEB SEARCH
    #
    # Wikipedia first
    # Google fallback
    # ========================================================

    result = smart_search(
        command
    )


    save_command(
        command,
        result.get(
            "response",
            "",
        ),
    )


    print(
        f"Final search type: "
        f"{result.get('type')}"
    )

    print("=" * 70)


    return jsonify(result)


# ============================================================
# HISTORY
# ============================================================

@app.get("/history")
def history_api():

    if database is None:

        return jsonify({

            "success": False,

            "history": [],

            "response": (
                "Database is not available."
            ),

        }), 503


    try:

        history = (
            database.get_history()
        )


        if not isinstance(
            history,
            list,
        ):

            history = []


        return jsonify({

            "success": True,

            "history": history,

        })


    except Exception as error:

        print(
            f"History error: {error}"
        )


        return jsonify({

            "success": False,

            "history": [],

            "response": (
                "Unable to load "
                "command history."
            ),

        }), 500


# ============================================================
# OPTIONS
# ============================================================

@app.route(
    "/<path:path>",
    methods=["OPTIONS"],
)
def handle_options(path):

    return "", 204


# ============================================================
# 404
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return jsonify({

        "success": False,

        "response": (
            "API endpoint not found."
        ),

    }), 404


# ============================================================
# 405
# ============================================================

@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({

        "success": False,

        "response": (
            "HTTP method not allowed."
        ),

    }), 405


# ============================================================
# 500
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({

        "success": False,

        "response": (
            "Internal server error."
        ),

    }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    host = os.getenv(
        "FLASK_HOST",
        "127.0.0.1",
    )


    port = int(
        os.getenv(
            "FLASK_PORT",
            "5000",
        )
    )


    debug = (
        os.getenv(
            "FLASK_DEBUG",
            "true",
        ).lower()
        == "true"
    )


    print()
    print("=" * 70)
    print(
        "              PERSONAL ASSISTANT API"
    )
    print("=" * 70)

    print(
        f"Server:   http://{host}:{port}"
    )

    print(
        f"Frontend: {frontend_url}"
    )

    print(
        f"Debug:    {debug}"
    )

    print(
        "Wikipedia: Enabled"
    )

    print(
        "Google:    Enabled"
    )

    print("=" * 70)
    print()


    app.run(
        host=host,
        port=port,
        debug=debug,
    )