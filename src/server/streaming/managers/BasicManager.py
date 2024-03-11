import threading
import time
import datetime

from queue import Queue
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from database import QueueInterface, Session
from ..VideoStreamer import VideoStreamer

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
        # should not be used from the worker thread
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

    def queue_to_telegram(self, start_idx=0, page_size=10):
        """
        Display the current playlist queue as an html formatted string,
        meant to be displayed in telegram
            - shows page_size videos at a time starting at start_idx
        """

        result = ""

        if self.db.is_empty(self.session):
            result = "<b>The queue is empty.</b>\nUse /add to add things to the queue"
        else:
            result = f"Queue ({datetime.timedelta(seconds=self.queue_get_length())})"

            for i, video in enumerate(
                self.db.get_range(start_idx, page_size, self.session)
            ):
                result += f"\n[{i}] {video}"
        return result

    """
    WORKER THREAD MANAGEMENT
    """

    def start_channel(self):
        """
        Start the channel worker thread
        """
        self.thread = threading.Thread(target=self.process_actions)
        self.thread.start()
        # TODO switch to a logger
        print(f"\t[Channel {self.channel_id}]: Started Worker thread")

    def stop_channel(self):
        """
        Stop the currently playing stream

        # TODO: does this remove channel from the bots channel list?
                should the bot even access the channel list?
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

            # run the action & then cleanup
            try:
                action.run(self)
            except Exception as e:
                print("process_action error", e)
            finally:
                action.cleanup()

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
        """
        Tell the streamer to play,
            - if streamer is empty tell it to start streaming
              if theres no new videos this wont do anything,
              but it should prevent deadlock
        """
        if self.streamer.empty:
            # if the streamer was empty we need to jumpstart it
            # ie itll grab a new video with get next
            self.streamer.stream()

        self.streamer.play()

    def pause(self):
        """
        Tell the streamer to pause
        """
        self.streamer.pause()

    def skip(self, amount=1):
        """
        Skip the given amount of songs starting with the currently playing song
        """
        # update the database by skipping the requested amount (ie just removing)
        skipped = self.db.skip(amount=amount)

        # now we tell the streamer there was a skip, so it stops playing the current one
        # and then asks for new content from the channel manager's get_next function
        self.streamer.skip()
        return skipped

    def add(self, video):
        """
        add video to queue.
            - If queue is empty & currently playing is none
              it gets played right away
            - otherwise its just added to the queue (history & queue entry made)
        """

        # TODO remove the test print
        print(f"\t[Manager] added video id: {video.id}")
        return

        # this is a reasonable place to start the downloads,
        # but how should it be formatted
        # TODO decide how to handle this, db video instance?

        # if its not currently playing anything, we will want to trigger it
        # then it will request the content with get_next
        if self.streamer.empty:
            self.streamer.stream()

        # already things in the queue

    def remove(self, idx: int):
        """
        remove the item at the specified position in the queue

        0 => currently paying song
        n => song n away from the top of the queue
        """

        return self.db.remove(idx=idx, session=self.session)

    # def add_to_playlist(self, video):
    #     if len(self.playlist) == 0:
    #         pass
    #     # TODO stop playing default screen
    #     self.playlist.append(video)

    # def remove_from_playlist(self, video):
    #     if video in self.playlist:
    #         self.playlist.remove(video)
