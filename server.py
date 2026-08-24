"""Amvera entry point for the English RPG web application."""

import os

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        workers=1,
    )
