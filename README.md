# Colloqium

## Prerequisites
- Python 3.10.12
- ngrok
- redis
- poetry

## Installation & Setup

1. Clone the repository:
git clone https://github.com/a1j9o94/AI-Phone-Bank-POC.git

2. Navigate to the project directory:
cd AI-Phone-Bank-POC

3. Install Poetry (Python's dependency manager):
pip install poetry

4. Install project dependencies:
poetry install

5. Set up APIs:
    - Create a Twilio account
    - Create a Twilio phone number
    - Create a Twilio API key and secret
    - Create a TwIML App and set the url to your deployment
    - Create OpenAI account and get API key
    - Create a Segment account and get WRITE_KEY
    - Create a Mixpanel account and get API secret

5. Activate the virtual environment:
poetry shell

6. Run the project:
python main.py

7. Run ngrok to expose the local server to Twilio:
ngrok http --domain=NGROK_DOMAIN_HERE 5000
## Troubleshooting

If you encounter any problems with the above steps, please open an issue in the repository or contact the maintainer at obletonadrian@gmail.com.

# Deployment

This project is currently deployed on Heroku. To deploy a new version, push to the `main` branch. Heroku will automatically deploy the new version. Be sure to set the environment variables appropriately in Heroku. Including everything mentioned above.

When deploying to Heroku, you will need a persistant database.

You will need to install the Poetry Buildpack to deploy to Heroku. https://github.com/moneymeets/python-poetry-buildpack

## Outstanding Issues

- [x] Add tracking with segment to follow conversations
- [x] Implement twilio callbacks to track call status
- [x] Implement simple report for campaign manager to review output of conversations
- [ ] Programatically generate Twilio phone numbers




