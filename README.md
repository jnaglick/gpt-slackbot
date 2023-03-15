# 🤖 ChatGPT Slackbot

Connects slack with chatGPT

## Setup:

1. Setup a venv: `python3 -m venv venv`
2. Use the venv: `source ./venv/bin/activate`
3. Install deps: `pip install -r requirements.txt`
4. Create env:   `cp .env.example .env`, fill out appropriate values
5. Run:          `python3 src/bot.py`
6. Integrate with slack. You can quickly prototype by either (1) using "Socket Mode" (2) running ngrok locally to get a public URL and using "Event Subscriptions"

## TODO:

- Move system and preamble to config (sorry @EconifyGPT)
- Make it run in the cloud

## IDEAS:

- @NobodyAskedGPT: Feed it all conversation text, but prompt to only give responses when certain topics are being discussed. Effect should be that the bot 'chimes in' without being prompted.