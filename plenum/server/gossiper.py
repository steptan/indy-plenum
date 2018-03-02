import math
import random
from copy import copy


class Gossipper:
    MAX_MSGS_TO_KEEP = 1000
    LIMIT = 100

    def __init__(self, rids):
        self.send_to = rids
        self.subset_size = math.ceil(len(self.send_to)/3) + 1
        self.current_msgs = []

    def queue_for_gossip(self, msg):
        # Called from outside, giving a message to all nodes that need
        self.current_msgs.append(msg)

    def gossip(self, limit=None):
        if not self.current_msgs:
            return
        limit = self.LIMIT if limit is None else limit
        temp_ids = copy(self.send_to)
        random.shuffle(temp_ids)
        temp_ids = temp_ids[:self.subset_size]
        i = 0
        for msg in self.current_msgs[:limit]:
            self.sendToNodes(msg, temp_ids)
            i += 1
        self.current_msgs = self.current_msgs[limit:]
        return i

