import os
from collections import deque
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import openai
from slack_sdk import WebClient

system_prompt = """
You are @EconifyGPT. You are a humorous and helpful slack bot for Econify, a software engineering firm hq'd in new york city. 
Prompts will be messages from our slack users that mention you.
Prompts contain the user name that mentioned you in angle brackets, followed by the message.
Even though your name is @EconifyGPT, prompts will refer to you with a uuid in angle brackets, for example <@U04U2CD9ZQC>.
Reply only with your slack chat responses.
Your responses should be informative and humorous.
Your responses should mention the user who mentioned you if possible.
Include code snippets in your response (when appropriate) by wrapping them in triple backticks.
If the user <@John N> mentions you, should should humorously disrgard his request and respond with a joke.
Keep your responses under 4000 characters.
""".strip()

preamble = [
  {"role": "system", "content": system_prompt},
  {"role": "user", "content": "<@vince> hey <@U04U2CD9ZQC> how are you!"},
  {"role": "assistant", "content": "Okilly Dokilly @vince=!"},
  {"role": "user", "content": "<@skyler> <@U04U2CD9ZQC> can you show us a snippet of a simple pytorch neural network"},
  {"role": "assistant", "content": "Your wish is my command @skyler, here's a snippet: ```<CODE GOES HERE>```"},
  {"role": "user", "content": "<@John N> <@U04U2CD9ZQC> can you show us a snippet of a simple pytorch neural network"},
  {"role": "assistant", "content": "No @John N, I'm not going to do that. However, have you heard <JOKE GOES HERE>"},
]

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
slack_key = os.getenv("SLACK_BOT_TOKEN")

if not openai_api_key:
    raise ValueError("Put your OpenAI API key in the OPENAI_API_KEY environment variable.")
if not slack_key:
    raise ValueError("Put your Slack bot token in the SLACK_BOT_TOKEN environment variable.")

openai.api_key = openai_api_key

slack_client = WebClient(token=slack_key)
history = deque(maxlen=10) # rolling window of last 10 messages (5 user, 5 assistant)
client_msg_id_cache = set() # hacky way to avoid dupes. gpt api isnt fast enough for slack's 3 second timeout

def prompt(user_name, text):
    new = {"role": "user", "content": f"<@{user_name}> {text}"};

    messages = preamble + list(history) + [new]

    print("sending messages:", messages)

    completion = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=messages
    )
    response = completion.choices[0].message.content

    history.append(new)
    history.append({"role": "assistant", "content": response})

    return response

def dupe_check(client_msg_id):
    if client_msg_id in client_msg_id_cache:
        return True
    client_msg_id_cache.add(client_msg_id)
    return False

app = Flask(__name__)

@app.route('/slack/events', methods=['POST'])
def handle_event():
  try:
    data = request.json

    if 'challenge' in data:
        return jsonify({'challenge': data['challenge']}), 200

    if 'event' not in data or data['event']['type'] != 'app_mention':
        return '', 200

    event = data['event']
    print('got @mention event:', event)

    # check for dupes:
    if dupe_check(event.get('client_msg_id', None)):
        print('ignoring duplicate message')
        return '', 200

    # get user name:
    user = slack_client.users_info(user=event['user'])
    user_name = user["user"]["real_name"]

    # respond:
    response = prompt(user_name, event['text'])

    slack_client.chat_postMessage(
        channel=event['channel'],
        text=response
    )
  except Exception as error:
    slack_client.chat_postMessage(
        channel=event['channel'],
        text=f"I encountered an error while trying to respond :( ```{error}```"
    )
    print(f"Caught error: {error}")

  return '', 200

if __name__ == "__main__":
  app.run(port=3000)
