from dotenv import load_dotenv
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from openai import OpenAI
import os

# Load environment variables
load_dotenv()

# Create OpenAI client (reads OPENAI_API_KEY from .env)
client = OpenAI()

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Chatbot</title>
      </head>
      <body style="font-family: Arial; margin: 40px;">
        <h1>Chatbot</h1>

        <form method="post" action="/chat">
          <input name="message" placeholder="Type here..." style="padding:10px; width:320px;" required />
          <button type="submit" style="padding:10px;">Send</button>
        </form>
      </body>
    </html>
    """

@app.post("/chat", response_class=HTMLResponse)
def chat(message: str = Form(...)):
    response = client.responses.create(
        model="gpt-5.2",
        input=message
    )

    reply = response.output_text

    return f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>Chatbot</title>
      </head>
      <body style="font-family: Arial; margin: 40px;">
        <h1>Chatbot</h1>

        <p><b>You:</b> {message}</p>
        <p><b>Bot:</b> {reply}</p>

        <form method="post" action="/chat">
          <input name="message" placeholder="Type again..." style="padding:10px; width:320px;" required />
          <button type="submit" style="padding:10px;">Send</button>
        </form>

        <p><a href="/">Back to home</a></p>
      </body>
    </html>
    """
