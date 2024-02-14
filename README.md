# weaving sounds
@tan.winn's art kinda project. We'll see~~~

1. [Directory Structure](#directory-structure)
2. [Set up dependencies](#set-up-dependencies)
3. [Host the API locally](#host-the-api-locally)
4. [Set up the Messenger Chatbot](#set-up-messenger-chatbot)
5. [Deploy the API to Gcloud](#deploy-the-app-to-gcloud)
6. [Troubleshooting](#troubleshooting)

## Directory structure
```
├── api
│   ├── __init__.py
│   ├── main.py             # Serves FastAPI APP
│   ├── datastore.py        # Database CRUD api
│   ├── utils.py            # Called by main
│   ├── pp.html             # privacy-policy HTML file
├── models                  # Data models by pydantic
│   ├── facebook.py         # Messenger chatbot
│   ├── weaver.py           # SoundThread DB
├── unittests
│   ├── data                # Test data
│   │   ├── facebook        # Messenger chatbot
│   │   ├── weaver          # SoundThread DB
│   ├── conftest.py         # Fixtures for test suites
│   ├── test_api.py         # main.py 
│   ├── test_datastore.py   # datastore.py
│   ├── test_models.py      # models.py
│   ├── test_utils.py       # utils.py
├── poetry.lock             # Dependency requirements
├── pyproject.toml          # Project configuration file
└── .gitignore  
└── .env                    # Environment variables

``````
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

## Host the API locally
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

- Webhook fields > `messages`
- Generate Access Token > Add the page you wanted to integrate the chatbot with
- Then press Token > Generate > generated the `<fb_page_token>` and updated it to `.env`

The app can now be tested by test users (if in Development) or the public (if Published).

### Test webhooks E2E
- Go to app Dashboard https://developers.facebook.com/apps/
- Webhooks fields > Test

## Set up Mongo Database locally
- Download the community version [here](https://www.mongodb.com/try/download/community)
- More instructions at [official MongoDBdocs](https://www.mongodb.com/docs/manual/tutorial/manage-mongodb-processes/)
```
cd weaving-sounds
mongod --dbpath voices/mongo --port 27017
```
## Deploy the app to GCloud
TBD


## Troubleshooting
### Messenger API Webhook verification fails
- Make sure your security variables including `FB_VERIFY_TOKEN` and
`FB_PAGE_TOKEN` are set correctly. Check [Environment variables not set correctly](#environment-variables-not-set-correctly) if your `echo $FB_PAGE_TOKEN` and the info set in `.env` mismatches. 
- Make sure your forwarding url using ngrok are correct if hosting locally. Any respawned of ngrok tunneling will require you to set yo the webhook verification again. 

### Environment variables not set correctly
If you edit the .env file, ensure it's properly loaded the the virtual env by reloading the venv
```
(in venv) exit  # Exit the venv
poetry shell  # Spawn the venv again
echo $FB_VERIFY_TOKEN  # Check the venv var
```
