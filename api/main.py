"""
api.main.py
"""
import logging
import os
import pickle
from contextlib import asynccontextmanager
from pathlib import Path
from pprint import pformat as pf

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse

from api import datastore, utils
from models import facebook

LOGGER = logging.getLogger(__name__)

# A user secret to verify webhook get request
FB_VERIFY_TOKEN = os.environ.get("FB_VERIFY_TOKEN", "default")
PRIVACY_POLICY_PATH = Path(__file__).joinpath("..").resolve() / "pp.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic for the API."""
    # startup Database client
    datastore.startup()
    datastore.clearall()
    datastore.clearvoices()
    yield
    # shutdown Database client
    datastore.shutdown()


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
    LOGGER.info(f"Data event:\n {pf(data.model_dump())}")
    for entry in data.entry:
        messages = entry.messaging
        answer = ""
        id = None
        if messages[0]:
            message = messages[0]
            LOGGER.info(f"userID: {message.sender.id}")
            LOGGER.info(f"Message object: \n{pf(message.message.model_dump())}")
            try:
                # Retrieve the public Facebook profile of the sender to store in system
                id = utils.handle_fb_user(message.sender.id)
                answer = utils.handle_user_message(id, message.message)
            except Exception as e:  # todo: handling exceptions better
                answer = f"ERROR! {e}"
                LOGGER.error(f"ERROR:\n {e}")

        # Send a reply to the sender
        utils.reply_to(message.sender.id, answer)
        return "Success!"


@APP.get("/privacy-policy", response_class=HTMLResponse)
def get_privacy_policy():
    """
    Privacy policy page. Needed according to Meta's app policy at https://www.termsfeed.com/blog/privacy-policy-url/
    """
    with open(PRIVACY_POLICY_PATH) as rfile:
        return rfile.read()


@APP.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles pydantic model validation error"""
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    LOGGER.error(
        f"Validation Exception with input: {pf(exc.errors()[0]['input'])}\n\n{pf(exc.errors()[0])}\n"
    )
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(content=content, status_code=422)


@APP.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handles general error"""
    LOGGER.error(f"{request.json()} :: {exc}")

    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    return JSONResponse(
        content={"status_code": 10422, "message": exc_str, "data": None},
        status_code=500,
    )
