# weaving sounds
@tan.winn

## Set up dependencies
We use `poetry` for depdency management but you can also use `venv` (vanilla) or `pipenv`
.env
```
FB_VERIFY_TOKEN = <your_verify_token>
FB_PAGE_TOKEN = <fb_page_token>
```

```
poetry shell
poetry install
```

## Host the bot locally
#### Spin up the server locally
```
uvicorn api.main:APP --reload  # Spin up the server
```
#### Set up tunneling for localhost
Follow instructions in https://ngrok.com/download to download ngrok
```
ngrok http <port>  
```
This will generate a forwarding url like `forwarding-url.ngrok-free.app`

## Set up Messenger chatbot
- Create/update app in Dashboard https://developers.facebook.com/apps/
- Products > Messenger API Settings
- Configure webhooks > Edit the following fields

    - Callback URL: `<forwarding-url.ngrok-free.app>/webhook`

    - Verify Token: `<your_verify_token> set in .env`

- Webhook fields > `message_deliveries`, `message_reads`, `messages`, `messaging_postbacks`
- Generate Access Token > Add the page you wanted to integrate the chatbot with
- Then press Token > Generate > generated the `<fb_page_token>` and updated it to `.env`

The app can now be tested by test users (if in Development) or the public (if Published).

## Deploy it to GCloud Compute Engine