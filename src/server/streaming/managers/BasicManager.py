import threading
import datetime
import logging

from queue import Queue

from database import QueueInterface, Session, History
from ..streamers.AiortcStreamer import  AiortcStreamer as VideoStreamer

import logging

logger = logging.getLogger(__name__)

# from database import QueueInterface, History, Video

# at what point does downloading happen?
# that should probably be managed by the channel?
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
        flag,
        host,
        port,
    ):

        self.title = title
        self.flag = flag
        self.channel_id = channel_id

        # the thread that the video streamer will be running in
        # gotta be seperate so we dont hold up reactions
        self.thread = None

        # make a session for this instance to interact with the db
        # should not be used from the worker thread, stick with the action sessions there
        self.session = Session()

        # queue holds all songs (currently playing should be position 0)
        self.db = QueueInterface(channel_id)

        # queue of interactions to handle
        self.actionQueue = Queue()

        # the streamer instance which will stream all of the vids
        self.streamer = VideoStreamer(
            host=host, port=port, get_next=self.dequeue, peek=self.get_current
        )

    """
    QUEUE MANAGEMENT
    """

    def get_current(self, session=None):
        """
        Get the currently playing video from the queue
        """

        if session is None:
            # TODO think of a better format for this
            self.session.close()
            self.session = Session()
            session = self.session

        return self.db.peek(session=session)

    def get_playlist(self, session=None):
        if session is None:
            self.session.close()
            self.session = Session()
            session = self.session

        # get the next 10

        return [q.history.video for q in self.db.get_range(amount=10, session=session)]

    def dequeue(self, event=None, session=None):
        """
        dequeue the front of the playlist
        """

        if session is None:
            self.session.close()
            self.session = Session()
            session = self.session

        logger.info(f"[Channel {self.channel_id}]: dequeueing")
        next = self.db.dequeue(session)

        # TODO send telegram message here that new one is playing

        if next is None:
            return None
        return next.history.video

    """
    BOT HELPERS
    """

    def queue_get_length(self, session=None):
        """
        Calculate the total remaining time in the playlist,
        including time left in the current video
        """

        if session is None:
            self.session.close()
            self.session = Session()
            session = self.session

        remaining_time = self.db.total_time(session)

        # if theres a currently playing vid get the remaining time
        if not self.streamer.empty:
            remaining_time += self.streamer.get_remaining()

        return remaining_time

    def queue_to_telegram(
        self, start=0, page=None, page_size=20, all=False, session=None, **kwargs
    ):
        """
        Display the current playlist queue as an html formatted string,
        meant to be displayed in telegram
            - shows page_size videos at a time starting at start
        """

        if session is None:
            self.session.close()
            self.session = Session()
            session = self.session

        if page is not None:
            start = page * page_size

        if all:
            start = 0
            page_size = self.db.length(session)

        result = ""

        if self.db.is_empty(session):
            result = "<b>The queue is empty.</b>\nUse /add to add things to the queue"
        else:
            result = (
                f"<b>Queue ({self.db.length(session)} songs: "
                f"{datetime.timedelta(seconds=self.queue_get_length(session=session))}):</b>\n"
            )

            for i, video in enumerate(
                self.db.get_range(start, page_size, session=session)
            ):
                result += f"\n{video.telegram_str()}"
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
        logging.info(f"[Channel {self.channel_id}]: Started Worker thread")

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

        self.streamer.stream()

        while True:
            # wait until there is an action
            action = self.actionQueue.get()

            # run the action & then cleanup
            try:
                action.run(self)
            except Exception as e:
                logger.error("process_action error", e)
                action.send_error(e)
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
        # TODO return false if already playing & true otherwise
        return True

    def pause(self):
        """
        Tell the streamer to pause

        - returns false if already paused or empty & true otherwise
        """
        paused_playback = self.streamer.pause()

        return paused_playback

    def add(self, video, user, session):
        """
        add video to queue.
            - If queue is empty & currently playing is none
              it gets played right away
            - otherwise its just added to the queue (history & queue entry made)

        video:      Video to add to the queue
        session:    sqlalchemy session to use, should not be channelmanager session
        """

        # make history instance and slap into the queue
        history = History.create(
            video.id, user.id, self.channel_id, datetime.datetime.now(), session=session
        )
        self.db.enqueue(history.id, session=session)

        # this is a reasonable place to start the downloads,
        # but how should it be formatted
        # TODO decide how to handle this, db video instance?

        # if its not currently playing anything, we will want to trigger it
        # then it will request the content with get_next
        # TODO play with the streamer
        if self.streamer.empty:
            self.streamer.stream()

        return history

        # already things in the queue

    def skip(self, session, amount=1) -> list[any]:
        """
        Skip the given amount of songs starting with the currently playing song

        session: sqlalchemy session to use, should not be channelmanager session
        """

        if session is None:
            session = self.session

        # update the database by skipping the requested amount (ie just removing)
        skipped = self.db.skip(amount=amount, session=session)

        # now we tell the streamer there was a skip, so it stops playing the current one
        # and then asks for new content from the channel manager's get_next function
        self.streamer.skip()
        return skipped

    def remove(self, idx: int, session) -> list[any]:
        """
        remove the item at the specified position in the queue

        0 => currently paying song
        n => song n away from the top of the queue
        """
        if idx == 0:
            # preform a skip instead
            return self.skip(session)

        # not playing so we dont need any fancy logic
        return [self.db.remove(idx=idx, session=self.session)]
