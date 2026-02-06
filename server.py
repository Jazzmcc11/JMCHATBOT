from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load env vars
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BALL_API_KEY = os.getenv("BALLDONTLIE_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Simple in-memory convo memory
conversation_memory = []

# ---------- HELPERS ----------

def get_today_nba_games() -> str:
    """
    Ball Don't Lie: get games for today.
    Returns a human-readable string for Big Sis to use.
    """
    url = "https://api.balldontlie.io/v1/games"

    # Many Ball Don't Lie keys work as plain Authorization value.
    # If yours requires Bearer, change to: {"Authorization": f"Bearer {BALL_API_KEY}"}
    headers = {"Authorization": BALL_API_KEY} if BALL_API_KEY else {}

    today = datetime.now().strftime("%Y-%m-%d")
    params = {"dates[]": today, "per_page": 100}

    try:
        res = requests.get(url, headers=headers, params=params, timeout=8)
        res.raise_for_status()
        data = res.json()

        games = data.get("data", [])
        if not games:
            return f"I checked {today} — no NBA games tonight."

        lines = []
        for g in games[:8]:
            home = g["home_team"]["full_name"]
            away = g["visitor_team"]["full_name"]
            status = g.get("status") or ""
            lines.append(f"{away} @ {home} — {status}")

        return "Tonight’s games:\n- " + "\n- ".join(lines)

    except requests.Timeout:
        return "I tried to check the slate but the sports feed timed out. Try again in a minute."
    except requests.HTTPError:
        # safe error message (no stack trace in UI)
        return f"I tried to check the slate but Ball Don’t Lie hit an HTTP error ({res.status_code})."
    except Exception:
        return "I tried to check the games but the sports feed acting funny right now."


def big_sis_prompt(user_message: str) -> str:
    memory_text = "\n".join(conversation_memory[-6:])
    return f"""
You are Big Sis Studio — a stylish, warm, tomboy-chic Black big sister.
Your vibe:
- supportive, never preachy
- sneakerhead energy
- music, sports, moodboard aware
- concise but thoughtful
- talks like a real person, not an essay

Conversation so far:
{memory_text}

User just said:
{user_message}

Respond naturally with fit advice, vibe guidance, or next-step questions.
"""


def is_sports_intent(text: str) -> bool:
    t = text.lower()
    keywords = ["nba", "game", "games", "matchup", "who plays", "tonight", "schedule"]
    return any(k in t for k in keywords)

# ---------- ROUTES ----------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Serves the UI page
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/chat")
async def chat(message: str = Form(...), mode: str = Form("fit")):
    """
    IMPORTANT: This route returns JSON because index.html calls res.json().
    """
    conversation_memory.append(f"You: {message}")

    if mode == "sports" or is_sports_intent(message):
        sports_info = get_today_nba_games()
        reply = (
            f"Aight, game night energy 🏀\n\n"
            f"{sports_info}\n\n"
            f"Now tell me — courtside, nosebleeds, or couch watch? I’ll build the fit around that."
        )
    else:
        response = client.responses.create(
            model="gpt-5.2",
            input=big_sis_prompt(message),
        )
        reply = (response.output_text or "").strip() or "Say that again sis—my brain just bufferin’ 😭"

    conversation_memory.append(f"Big Sis Studio: {reply}")

    # ✅ what your frontend expects:
    return JSONResponse({"reply": reply})


@app.post("/reset")
async def reset():
    """
    Your Reset button calls this. Also returns JSON.
    """
    conversation_memory.clear()
    return JSONResponse({"ok": True})
