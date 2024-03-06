import threading
import time
import datetime

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from ..VideoStreamer import VideoStreamer
from ..Video import Video
from queue import Queue

from database import QueueInterface, Session

# from database import QueueInterface, History, Video

# at what point does downloading happen?
# that shoul;d probably be managed by the channel?
#  - make a thread for the channel devoted to downloading
#  - make a thread for all channels for downloading


class BasicManager:
    """
    Class which manages all of the streaming functionality of a single channel
    - manages a worker thread which
        - does actual streaming via an instance of "VideoStreamer"
        - watches a queue "actionQueue" which other parts of the server can send actions to (namely the bot)
    - the channel queue with interactions with the database through "QueueInterface"
    - sending messages to the telegram chats
    """

    def __init__(
        self,
        channel_id,
        title,
        host,
        port,
    ):
        # the streamer instance which will stream all of the vids
        self.streamer = VideoStreamer(host=host, port=port, get_next=self.get_next)

        self.title = title
        self.channel_id = channel_id

        # the thread that the video streamer will be running in
        # gotta be seperate so we dont hold up reactions
        self.thread = None

        # make a session for this instance to interact with the db
        self.session = Session()

        # queue holds all songs (currently playing should be position 0)
        self.db = QueueInterface(channel_id)

        # queue of interactions to handle
        self.actionQueue = Queue()

    """
    QUEUE MANAGEMENT
    """

    def get_current(self):
        """
        Get the currently playing video from the queue
        """
        # TODO map queue obj to video instance
        return self.db.peek(self.session)

    def get_next(self):
        """
        get the next element out of the queue,
        while also removing the front
        """

        # this dequeue returns the new head, so it also does the next element
        next = self.db.dequeue(self.session)
        print(next)

        return next

    """
    BOT HELPERS
    """

    def queue_get_length(self):
        """
        Calculate the total remaining time in the playlist,
        including time left in the current video
        """
        remaining_time = self.db.total_time(self.session)

        # if theres a currently playing vid get the remaining time
        if not self.streamer.empty:
            remaining_time += self.streamer.get_remaining()

        return remaining_time

    def queue_to_html(self, start_idx=0, page_size=10):
        """
        Display the current playlist queue as an html formatted string,
        showing page_size videos at a time
        """

        result = ""

        if self.db.is_empty(self.session):
            result = "<b>The queue is empty.</b>\nUse /add to add things to the queue"
        else:
            result = f"Queue ({datetime.timedelta(seconds=self.queue_get_length())})"
            # TODO add the total time
            # for i, video in enumerate(self.playlist[start_idx : start_idx + page_size]):
            #     result += f"\n[{i}] {video}"
        return result

    """
    WORKER THREAD MANAGEMENT
    """

    def start_channel(self):
        self.thread = threading.Thread(target=self.process_actions)
        self.thread.start()
        print(f"\t[Channel {self.channel_id}]: Started Worker thread")

    def stop_channel(self):
        """
        Stop the currently playing stream

        # TODO: does this remove channel from like the bots channel list?
        """
        if self.thread and self.thread.is_alive():
            self.streamer.kill()
            self.thread.join()

    def process_actions(self):
        """
        Start the video stream and then process incoming actions
        """

        while True:
            # wait until there is an action
            action = self.actionQueue.get()

            print("Channel: processing action")
            print(action)

            # run the action
            action.run(self)

    """
    STREAM ACTIONS
    """

    def send_action(self, action):
        """
        Add action to the actionQueue, which will then
        be processed by the worker thread of the channel
        """
        self.actionQueue.put(action)

    def play(self):
        if self.current is None and len(self.queue) > 0:
            # if current is empty and there is item in queue
            # think that would imply its not got any going currently, but should idk
            self.streamer.stream()

        self.streamer.play()

    def pause(self):
        self.streamer.pause()

    def skip(self, amount=1):
        """
        Skip the given amount of songs starting with the currently playing song
        """
        # update the queues
        skipped = self.queue[0 : amount - 1]
        self.queue = self.queue[amount - 1 :]
        self.db.skip(amount=amount)

        # videostreamer asks for next, which will have accounted for the skipped already
        self.streamer.skip()
        return skipped

    def add(self, video: Video):
        """
        add video to queue. If queue is empty & currently playing is none
        it gets played right away
        """

        # this is a reasonable place to start the downloads, but how
        # should it be formatted
        self.queue.append(video)
        Users.add_play(video.length, video.user_id)
        self.db.add(video.get_id(), video.title, video.length, video.url, video.user_id)

        # if its not currently playing anything
        # TODO make a moore competent check lol
        if self.streamer.empty:
            #
            self.streamer.stream()

        # already things in the queue

    def remove(self, idx: int):
        """
        remove the item at the specified position in the queue

        -1 => currently paying song, technically not in queue,
              but include for conciseness
        0 => next song (top of queue)
        n => song n away from the top of the queue
        """
        if idx == -1:
            return self.skip()

        vid = self.queue[idx]
        del self.queue[idx]
        self.db.remove(idx)
        return vid

    # def add_to_playlist(self, video):
    #     if len(self.playlist) == 0:
    #         pass
    #     # TODO stop playing default screen
    #     self.playlist.append(video)

    # def remove_from_playlist(self, video):
    #     if video in self.playlist:
    #         self.playlist.remove(video)
