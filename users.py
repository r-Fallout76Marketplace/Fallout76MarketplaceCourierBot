import time


# Users class
# Stores important information and calculates if cool down time has expired
class Users:

    # Constructor
    def __init__(self, comment):
        # comment
        self.comment = comment
        # Author of comment
        self.author = self.comment.author

        # Submission
        self.submission = self.comment.submission
        # Submission Author
        self.submission_author = self.submission.author

        # time_requested
        self.time_utc = comment.created_utc

    # Compares the authors name and submissions
    def is_cool_down_expired(self):
        now = time.time()
        age = now - self.time_utc

        # cool down expires after 30 minutes
        if age > 1800:
            return True
        else:
            return False

    # compares two user objects
    def __cmp__(self, other):
        if self.author == other.author:
            if self.submission == other.submission:
                return True
        return False
