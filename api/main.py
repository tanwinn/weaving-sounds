"""
api.main.py
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from pprint import pformat as pf

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from api import datastore, utils
from models import facebook

LOGGER = logging.getLogger(__name__)

# A user secret to verify webhook get request
FB_VERIFY_TOKEN = os.environ.get("FB_VERIFY_TOKEN", "default")
PRAVICY_POLICY_PATH = Path(__file__).joinpath("..").resolve() / "pp.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic for the API."""
    datastore.load_memory_from_storage()
    yield
    datastore.load_storage_from_memory()


APP = FastAPI(
    title="Weaving Sounds Digital Archive Bot",
    description="A Chatbot that archive daily sounds",
    docs_url="/",
    redoc_url="/docs",
    version="0.0.32",
    lifespan=lifespan,
)


@APP.get("/webhook")
async def messenger_webhook(request: Request):
    """
    A webhook to return a challenge
    """
    verify_token = request.query_params.get("hub.verify_token")
    # check whether the verify tokens match

    if (
        verify_token == FB_VERIFY_TOKEN
        and request.query_params.get("hub.mode") == "subscribe"
    ):
        # respond with the challenge to confirm
        try:
            resp = int(request.query_params.get("hub.challenge", "errored"))
        except ValueError:
            resp = request.query_params.get("hub.challenge", "errored")
        LOGGER.warning(f"Return challenge: {resp}")
        return JSONResponse(content=resp, headers={"Content-Type": "text/html"})
    LOGGER.error(
        f"""Invalid Request or Verification Token: given {verify_token}, expected {FB_VERIFY_TOKEN}.
        Have you set up the token based on README/Set up Messenger chatbot?"""
    )
    return "Invalid Request or Verification Token"


@APP.post("/webhook")
async def messenger_post(data: facebook.Event) -> str:
    """
    Handler for webhook Facebook Event (currently for postback and messages)
    """
    LOGGER.warning(f"Data event:\n {pf(data.model_dump())}")
    for entry in data.entry:
        messages = entry.messaging
        if messages[0]:
            message = messages[0]
            LOGGER.warning(f"Message object: \n{pf(message.message.model_dump())}")
            _ = utils.handle_user_message(message.message)
            # We retrieve the Facebook user ID of the sender
            # fb_id = message.sender.id
    return "Success!"


@APP.get("/privacy-policy", response_class=HTMLResponse)
def get_privacy_policy():
    with open(PRAVICY_POLICY_PATH) as rfile:
        return rfile.read()
