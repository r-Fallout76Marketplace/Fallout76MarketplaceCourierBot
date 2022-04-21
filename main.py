import json
import os
import re
import time
import traceback

import praw
import prawcore
import requests
import schedule

import bot_responses
import users

# Login Api
reddit = praw.Reddit(client_id=os.environ['client_id'],
                     client_secret=os.environ['client_secret'],
                     username=os.environ['username'],
                     password=os.environ['password'],
                     user_agent=os.environ['user_agent'])

# Only works in the subreddit mentioned in CONFIG and when bot is mentioned explicitly
subreddit = reddit.subreddit(os.environ['subreddit_name'])

# Gets 100 historical comments
comment_stream = subreddit.stream.comments(pause_after=-1, skip_existing=True)

# The numbers of failed attempt to connect to reddit
failed_attempt = 1

# cool down_memory so people don't send repeated requests
cool_down_memory = {}


# Delete the users whose cool down have expired
def refresh_memory():
    for key, value in list(cool_down_memory.items()):
        if value.is_cool_down_expired():
            del cool_down_memory[key]


# Send message to discord channel
def send_message_to_discord(message_param):
    data = {"content": message_param, "username": os.environ['bot_name']}
    output = requests.post(os.environ['discord_webhook'], data=json.dumps(data),
                           headers={"Content-Type": "application/json"})
    output.raise_for_status()


schedule.every(30).minutes.do(refresh_memory)
print('Bot has started running...')


# Checks if the user_obj is in cool_down memory
# If it in memory checks if the timer is up or not
def search_in_cool_down_memory(author_name):
    if author_name in cool_down_memory.keys():
        user_obj = cool_down_memory[author_name]
        if user_obj.is_cool_down_expired():
            return False
        else:
            return True
    else:
        return False


# Make sure bot run forever
def send_error_message_to_discord(tb):
    data = {"content": tb, "username": os.environ['bot_name']}
    output = requests.post(os.environ['error_message_webhook'], data=json.dumps(data),
                           headers={"Content-Type": "application/json"})
    output.raise_for_status()


while True:
    try:
        schedule.run_pending()
        # Gets comments and if it receives None, it switches to posts
        for comment in comment_stream:
            if comment is None or comment.author.name == "AutoModerator":
                break
            courier_trigger_keyword = r"^(!COURIER|COURIER!)"
            if re.search(courier_trigger_keyword, comment.body, re.IGNORECASE) is not None:
                # Check if the submission flair is right
                regex = re.compile('XBOX|Price Check XBOX|PlayStation|Price Check PS|PC|Price Check PC', re.IGNORECASE)
                submission_flair_text = comment.submission.link_flair_text
                match = re.match(regex, str(submission_flair_text))
                if match is not None:
                    # Check if the user is still in cool down
                    if search_in_cool_down_memory(comment.author.name):
                        bot_responses.still_in_cool_down(comment)
                    else:
                        user_obj = users.Users(comment)
                        cool_down_memory[comment.author.name] = user_obj
                        bot_responses.request_sent_successfully(comment)

                        if "xbox" in submission_flair_text.lower():
                            console_type = "Xbox"
                        elif "playstation" in submission_flair_text.lower() or "PS" in submission_flair_text.lower():
                            console_type = "Playstaion"
                        elif "pc" in submission_flair_text.lower():
                            console_type = "PC"
                        else:
                            console_type = "Mod"

                        message = f"@{console_type}[u/{comment.author.name}](https://www.reddit.com{comment.submission.permalink}) " \
                                  f"is requesting courier service. Please react to the message accordingly. " \
                                  f"<:request_completed:803477382156648448> (request completed), " \
                                  f"<:request_inprocess:804224025688801290> (request in process), " \
                                  f"<:request_expired:803477444581523466> (request expired), and " \
                                  f"<:request_rejected:803477462360784927> (request rejected). "
                        send_message_to_discord(message)
                # send comment if the submission is of wrong type
                else:
                    bot_responses.not_valid_submission(comment)
    except Exception as exception:
        # Sends a message to mods in case of error
        tb = traceback.format_exc()
        try:
            send_error_message_to_discord(tb)
            print(tb)
        except Exception:
            print("Error sending message to is_fake_Account")

        # In case of server error pause for two minutes
        if isinstance(exception, prawcore.exceptions.ServerError):
            print("Waiting {} minutes".format(2 * failed_attempt))
            # Try again after a pause
            time.sleep(120 * failed_attempt)
            failed_attempt = failed_attempt + 1

        # Refresh streams
        comment_stream = subreddit.stream.comments(pause_after=-1, skip_existing=True)
