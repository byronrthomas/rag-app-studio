# A historic chat record is just a list of dicts where each dict has a "role" key and a "content" key. The "role" key is either "user" or "assistant" or "system". The "content" key is the text of the message.
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def hashable_representation(chat_messages: List[Dict[str, str]]):
    # Convert each dictionary in the list to a sorted tuple of tuples
    # Flatten the list of lists into a single list of tuples before converting to a tuple
    flat_list_of_tuples = [tuple(sorted(record.items())) for record in chat_messages]
    tuple_representation = tuple(flat_list_of_tuples)
    return tuple_representation


def hash_chat_record(chat_messages: List[Dict[str, str]]):
    # Get the hashable representation
    hashable_repr = hashable_representation(chat_messages)
    # Hash the immutable structure
    return hash(hashable_repr)


# A user chat history is a class that stores a latest-first time-ordered list of historic chat records.


class UserChatHistory:
    def __init__(self):
        self.historic_chat_record_hashes = {}
        self.chat_records = []

    def update_chat_history(self, prev_messages, new_question, new_answer):
        # Hash the prev_messages to work out whether this is a new chat record
        prev_messages_hash = hash_chat_record(prev_messages)
        if prev_messages_hash in self.historic_chat_record_hashes:
            # Remove the key - we are going to place a new one
            del self.historic_chat_record_hashes[prev_messages_hash]
        new_chat_record = prev_messages + [new_question, new_answer]
        new_chat_record_hash = hash_chat_record(new_chat_record)
        self.historic_chat_record_hashes[new_chat_record_hash] = True
        self.chat_records.insert(
            0, {"key": new_chat_record_hash, "messages": new_chat_record}
        )

    def get_chat_records(self):
        return [
            r for r in self.chat_records if r["key"] in self.historic_chat_record_hashes
        ]

    def compact(self):
        self.chat_records = self.get_chat_records()


class ChatHistory:
    def __init__(self):
        self.user_chat_histories = {}

    def get_user_chat_history(self, user_id):
        if user_id not in self.user_chat_histories:
            return []
        return self.user_chat_histories[user_id].get_chat_records()

    def update_user_chat_history(
        self, user_id, prev_messages, new_question, new_answer
    ):
        logger.debug(
            "Updating chat history for user %s with %d previous messages",
            user_id,
            len(prev_messages),
        )
        if user_id not in self.user_chat_histories:
            self.user_chat_histories[user_id] = UserChatHistory()
        self.user_chat_histories[user_id].update_chat_history(
            prev_messages, new_question, new_answer
        )
        # self.user_chat_histories[user_id].compact()
        # return self.user_chat_histories[user_id].get_chat_records()
