import json
import os
import threading
from time import sleep
from traceback import format_exc
from typing import Callable

import requests
import schedule
from dotenv import load_dotenv
from praw import Reddit
from praw.exceptions import APIException

import bot_responses
import users

load_dotenv('config.env')


# Delete the users whose cool down have expired
def refresh_memory():
    for key, value in list(cool_down_memory.items()):
        if value.is_cool_down_expired():
            del cool_down_memory[key]


# Send message to discord channel
def send_message_to_discord(message_param):
    data = {"content": message_param, "username": os.getenv('bot_name')}
    output = requests.post(os.getenv('discord_webhook'), data=json.dumps(data),
                           headers={"Content-Type": "application/json"})
    output.raise_for_status()


# Checks if the user_obj is in cool_down memory
# If it in memory checks if the timer is up or not
def search_in_cool_down_memory(submission_id: str):
    if submission_id in cool_down_memory.keys():
        user_obj = cool_down_memory[submission_id]
        if user_obj.is_cool_down_expired():
            return False
        else:
            return True
    else:
        return False


def send_error_message_to_discord(exception_body: str):
    data = {"content": exception_body, "username": os.getenv('bot_name')}
    output = requests.post(os.getenv('error_message_webhook'), data=json.dumps(data),
                           headers={"Content-Type": "application/json"})
    output.raise_for_status()


def exception_wrapper(func: Callable[[Reddit], None]) -> Callable[[Reddit], None]:
    """Decorator to handle the exceptions and to ensure the code doesn't exit unexpectedly.
    :param func: function that needs to be called
    :returns: wrapper function
    :rtype: Callable[[Reddit, AsyncIOMotorClient], Awaitable[None]]
    """

    def wrapper(reddit_instance: Reddit) -> None:
        global cool_down_timer

        while True:
            try:
                func(reddit_instance)
            except APIException as praw_excep:
                send_error_message_to_discord(exception_body=format_exc())

                sleep(cool_down_timer)
                cool_down_timer = (cool_down_timer + 30) % 360
                print(f"Cooldown: {cool_down_timer} seconds")
            except Exception as general_exc:
                send_error_message_to_discord(exception_body=format_exc())

                sleep(cool_down_timer)
                cool_down_timer = (cool_down_timer + 30) % 360
                print(f"Cooldown: {cool_down_timer} seconds")

    return wrapper


@exception_wrapper
def request_listener(reddit: Reddit):
    subreddit = reddit.subreddit(os.getenv('subreddit_name'))
    for comment in subreddit.stream.comments(skip_existing=True):
        if comment.author.name == "AutoModerator":
            continue

        if comment.body.upper().startswith(("!COURIER", "COURIER!")):
            submission_flair_text: str = comment.submission.link_flair_text
            if submission_flair_text.startswith(("XBOX", "PlayStation", "PC", "Price")):
                # Check if the user is still in cool down
                if search_in_cool_down_memory(comment.submission.id):
                    bot_responses.still_in_cool_down(comment)
                else:
                    user_obj = users.Users(comment)
                    cool_down_memory[comment.submission.id] = user_obj
                    bot_responses.request_sent_successfully(comment)

                    if "xbox" in submission_flair_text.lower():
                        console_type = "<@&794246049278591007>"
                    elif "playstation" in submission_flair_text.lower() or "PS" in submission_flair_text.lower():
                        console_type = "<@&794245851743518730>"
                    elif "pc" in submission_flair_text.lower():
                        console_type = "<@&794246168288034856>"
                    else:
                        console_type = "Mod"

                    message = f"{console_type} [u/{comment.author.name}](https://www.reddit.com{comment.submission.permalink}) " \
                              f"is requesting courier service. Please react to the message accordingly. " \
                              f"<:request_completed:803477382156648448> (request completed), " \
                              f"<:request_inprocess:804224025688801290> (request in process), " \
                              f"<:request_expired:803477444581523466> (request expired), and " \
                              f"<:request_rejected:803477462360784927> (request rejected). "
                    send_message_to_discord(message)
            else:
                # send comment if the submission is of wrong type
                bot_responses.not_valid_submission(comment)


def main():
    reddit = Reddit(client_id=os.getenv('client_id'),
                    client_secret=os.getenv('client_secret'),
                    username=os.getenv('username'),
                    password=os.getenv('password'),
                    user_agent=os.getenv('user_agent'))
    request_listener(reddit)


def run_continuously(interval=1):
    """Continuously run, while executing pending jobs at each
    elapsed time interval.
    @return cease_continuous_run: threading. Event which can
    be set to cease continuous run. Please note that it is
    *intended behavior that run_continuously() does not run
    missed jobs*. For example, if you've registered a job that
    should run every minute, and you set a continuous run
    interval of one hour then your job won't be run 60 times
    at each interval but only once.
    """
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()
    return cease_continuous_run


if __name__ == '__main__':
    cool_down_timer = 0
    cool_down_memory = {}
    print('Bot has started running...')
    schedule.every(30).minutes.do(refresh_memory)
    stop_run_continuously = run_continuously()
    main()
