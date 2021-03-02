import prawcore


# Replies to comment with text=body
def reply(comment_or_submission, body):
    # Add disclaimer text
    response = body + "\n\n^(This action was performed by a bot, please contact the mods for any questions. "
    response += "[See disclaimer](https://www.reddit.com/user/Vault-TecTradingCo/comments/lkllre" \
                "/disclaimer_for_rfallout76marketplace/)) "
    try:
        new_comment = comment_or_submission.reply(response)
        new_comment.mod.distinguish(how="yes")
        new_comment.mod.lock()
    except prawcore.exceptions.Forbidden:
        pass


# If submission flair is not correct
def not_valid_submission(comment):
    comment_body = "Hi " + comment.author.name + "! You cannot request a courier on this type of submission. "
    comment_body += "The courier command only works on trading (PC, XBOX or PlayStation) and Price Checks posts."
    reply(comment, comment_body)


# Replies to user if the user is still in cool down
def still_in_cool_down(comment):
    comment_body = "Hi " + comment.author.name + "! Your 30 minutes cool down timer hasn't finished yet. You can "
    comment_body += "submit courier request once every 30 minutes. If within 30 minutes no one reaches you out. You "
    comment_body += "may submit another request."
    reply(comment, comment_body)


# Replies to user if the request is successful
def request_sent_successfully(comment):
    comment_body = "Hi " + comment.author.name + "! The bot has successfully sent your courier request. A courier will "
    comment_body += "reach you out in 30 minutes. If you don't get a response even after 30 minutes, you may submit "
    comment_body += " another request."
    reply(comment, comment_body)
