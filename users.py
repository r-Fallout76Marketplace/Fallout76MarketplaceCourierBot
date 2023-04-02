import time
from dataclasses import dataclass

from praw.models import Comment, Redditor, Submission


@dataclass
class Users:
    comment: Comment
    author: Redditor = None
    submission: Submission = None
    submission_author: Redditor = None
    time_of_request: float = None

    def __post_init__(self):
        self.author = self.comment.author
        self.submission = self.comment.submission
        self.submission_author = self.submission.author
        self.time_of_request = self.comment.created_utc

    def is_cool_down_expired(self):
        now = time.time()
        age = now - self.time_of_request

        if age > 1800:
            return True
        else:
            return False

    def __eq__(self, other):
        if self.author == other.author and self.submission == other.submission:
            return True
        return False
