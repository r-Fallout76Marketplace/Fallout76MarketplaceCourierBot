import json
import re
import time
import traceback

import requests
import schedule

import CONFIG
import bot_responses
import users

# Only works in the subreddit mentioned in CONFIG and when bot is mentioned explicitly
subreddit = CONFIG.reddit.subreddit(CONFIG.subreddit_name)

# Gets 100 historical comments
comment_stream = subreddit.stream.comments(pause_after=-1, skip_existing=True)

# The numbers of failed attempt to connect to reddit
failed_attempt = 1

# cooldown_memory so people don't send repeated requests
cooldown_memory = []


# Delete the users whose cool down have expired
def refresh_memory():
    for user_obj_mem in cooldown_memory:
        if user_obj_mem.is_cool_down_expired():
            cooldown_memory.remove(user_obj_mem)


# Send message to discord channel
def send_message_to_discord(message_param):
    data = {"content": message_param, "username": CONFIG.username}
    output = requests.post(CONFIG.discord_webhook, data=json.dumps(data), headers={"Content-Type": "application/json"})
    output.raise_for_status()


schedule.every(1830).seconds.do(refresh_memory)
print('Bot has started running...')


# Checks if the user_obj is in cool_down memory
def search_in_cool_down_memory(user_obj):
    for user_obj_mem in cooldown_memory:
        if user_obj.__cmp__(user_obj_mem):
            return True
    return False


# Make sure bot run forever
while True:
    try:
        schedule.run_pending()
        # Gets comments and if it receives None, it switches to posts
        for comment in comment_stream:
            if comment is None or comment.author.name == "AutoModerator":
                break
            courier_trigger_keyword = r"!COURIER"
            if re.search(courier_trigger_keyword, comment.body, re.IGNORECASE) is not None:
                # Check if the submission flair is right
                regex = re.compile('XBOX|Price Check XBOX|PlayStation|Price Check PS|PC|Price Check PC', re.IGNORECASE)
                submission_flair_text = comment.submission.link_flair_text
                match = re.match(regex, str(submission_flair_text))
                if match is not None:
                    user_obj = users.Users(comment)
                    # Check if the user is still in cool down
                    if search_in_cool_down_memory(user_obj):
                        bot_responses.still_in_cool_down(comment)
                    else:
                        cooldown_memory.append(user_obj)
                        bot_responses.request_sent_successfully(comment)
                        message = "[u/" + comment.author.name + "](https://www.reddit.com"
                        message += comment.submission.permalink + ") is requesting courier service. Please react to "
                        message += "the message accordingly. "
                        message += "<:request_completed:803477382156648448> (request completed), "
                        message += "<:request_inprocess:804224025688801290> (request in process), "
                        message += "<:request_expired:803477444581523466> (request expired), and "
                        message += "<:request_rejected:803477462360784927> (request rejected). "
                        send_message_to_discord(message)
                # send comment if the submission is of wrong type
                else:
                    bot_responses.not_valid_submission(comment)
    except Exception:
        # Sends a message to mods in case of error
        tb = traceback.format_exc()
        try:
            CONFIG.reddit.redditor("is_fake_Account").message(CONFIG.subreddit_name, tb,
                                                              from_subreddit=CONFIG.subreddit_name)
            print(tb)
        except Exception:
            print("Error sending message to is_fake_Account")

        # Try again after a pause
        time.sleep(30 * failed_attempt)
        failed_attempt = failed_attempt + 1

        # Refresh streams
        comment_stream = subreddit.stream.comments(pause_after=-1, skip_existing=True)
