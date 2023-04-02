from __future__ import annotations

import prawcore
from praw.models import Comment


# Replies to comment with text=body
def reply(comment: Comment, body: str):
    # Add disclaimer text
    response = body + "\n\n^(This action was performed by a bot, please contact the mods for any questions. "
    response += "[See disclaimer](https://www.reddit.com/user/Vault-TecTradingCo/comments/lkllre" \
                "/disclaimer_for_rfallout76marketplace/)) "
    try:
        new_comment = comment.reply(response)
        new_comment.mod.distinguish(how="yes")
        new_comment.mod.lock()
    except prawcore.exceptions.Forbidden:
        pass


# If submission flair is not correct
def not_valid_submission(comment: Comment):
    comment_body = f"Hi u/{comment.author.name}! You cannot request a courier on this type of submission. " \
                   f"The courier command only works on trading (PC, XBOX or PlayStation) and Price Checks posts."
    reply(comment, comment_body)


# Replies to user if the user is still in cool down
def still_in_cool_down(comment: Comment):
    comment_body = f"Hi u/{comment.author.name}! Another user has already called for a courier on this submission. " \
                   f"You can submit a new request if no one reaches out to you within 30 minutes."
    reply(comment, comment_body)


# Replies to user if the request is successful
def request_sent_successfully(comment: Comment):
    comment_body = f"Hi u/{comment.author.name}! The bot has successfully sent your courier request. A courier will reach you out in 30 minutes. " \
                   f"If you don't get a response even after 30 minutes, you may submit another request."
    reply(comment, comment_body)
