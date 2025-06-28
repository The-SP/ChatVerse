# Real-Time Chat API

A FastAPI application providing real-time messaging, user authentication, and AI-powered conversation summaries.

## Getting Started

1. Clone the repository
2. Set up environment variables in `.env`:

   - Create a `.env` file and populate it with your actual API keys and Redis URL, using the `.env.sample` file as a template.

3. **Install dependencies:**

   - Using `uv`
     ```bash
     uv sync
     ```
   - Using `pip`
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     pip install -r pyproject.toml
     ```

4. **Set up PostgreSQL database:**
   - Ensure you have PostgreSQL running locally
   - Create a database that matches your `DB_NAME` in the `.env` file

## Run the Application

1. **Run locally:**
   ```bash
   uv run uvicorn app.main:app --reload
   ```
2. **Run with Docker:**
   ```bash
   docker-compose up
   ```

- The API will be accessible at `http://localhost:8000`.
- Interactive API documentation at `http://localhost:8000/docs`

## Features

- Real-time messaging with WebSocket connections
- User authentication (local and Google OAuth)
- Direct messaging between users
- AI-powered conversation summaries using Gemini API
- Message read status tracking
- User search functionality

## Technologies

- **Framework**: FastAPI with Python 3.x
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Real-time**: WebSocket connections for instant messaging
- **Authentication**: JWT tokens, OAuth2, Google OAuth
- **AI Integration**: LangChain with Google Gemini API
