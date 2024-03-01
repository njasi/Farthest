import threading
import time
import datetime

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from .VideoStreamer import VideoStreamer
from .Video import Video
from database.queue import Queue as QDB
from queue import Queue

# at what point does downloading happen?
# that shoul;d probably be managed by the channel?
#  - make a thread for the channel devoted to downloading
#  - make a thread for all channels for downloading


class Channel:
    def __init__(
        self,
        channel_id,
        host,
        port,
        queue=[],
    ):
        # the streamer instance which will stream all of the vids
        self.streamer = VideoStreamer(host=host, port=port)

        # the thread that the video streamer will be running in
        # gotta be seperate so we dont hold up reactions
        self.thread = None

        # manages the playlist, one an array of current video instances
        # and the other a jsondb for robustness & transition to history info
        self.current: Video = None
        # queues will hold all non playing songs
        self.queue = queue
        self.db = QDB(channel_id)
        # TODO load from db?

        self.actionQueue = Queue()

    """
    QUEUE MANAGEMENT
    """

    def get_current(self):
        return self.current

    def get_next(self):
        """
        get the next element out of the queue
        and update the db
        """
        next = None
        # update database by removing the top song
        # note that the db includes current while
        # self.queue does not, i think i got the
        # logic right here but its a bit annoying
        self.db.pop()
        self.db.update_current()

        if len(self.queue) > 0:
            next = self.queue[0]
            self.current = next
            self.queue = self.queue[1:]

        return next

    """
    BOT HELPERS
    """

    def queue_get_length(self):
        """
        Calculate the total remaining time in the playlist,
        including time left in the current video
        """
        remaining_time = 0
        for video in self.queue:
            remaining_time += video.length

        # if theres a currently playing vid get the remaining time
        if self.current is not None:
            remaining_time += self.streamer.get_remaining()

        return remaining_time

    def queue_to_html(self, start_idx=0, page_size=10):
        """
        Display the current playlist queue as an html formatted string,
        showing page_size videos at a time
        """

        result = ""
        if not self.playlist:
            result = "<>The queue is empty.</b>\nUse /add to add things to the queue"
        else:
            result = f"Queue ({datetime.timedelta(seconds=self.queue_get_length())})"
            # TODO add the total time
            for i, video in enumerate(self.playlist[start_idx : start_idx + page_size]):
                result += f"\n[{i}] {video}"
        return result

    """
    WORKER THREAD MANAGEMENT
    """

    def start_channel(self):
        self.thread = threading.Thread(target=self.process_actions)
        self.thread.start()

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

            # run the action
            action.run(self)

    """
    STREAM ACTIONS
    """

    def send_action(self, action):
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
        self.queue.add()
        self.db.add(
            video.get_id(),
            video.title,
            video.length,
            video.url,
            video.user_id,
        )

        # if not be currently playing
        if self.current is None and len(self.queue) == 0:
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


class ChannelAction:
    """
    class to bundle any channel action,
    idea is we pass it though to the thread in a queue of tasks

    id rather use a combined struct or smth but this is python so

    could pass a tuple but then the managing func would be rough
    with this we can pass values through & have distince actions

    and the worker thread processes them one by one
    """

    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
        # for communicating with telegram if needed
        # most actions will be triggered by an update after all
        self.update = update
        self.context = context

        # additional info
        self.created_at = time.time()
        self.__dict__.update(kwargs)

    def run(chan: Channel):
        pass


class Pause(ChannelAction):
    """
    action for pausing
    """

    def run(chan: Channel):
        chan.pause()


class Play(ChannelAction):
    """
    action for playing stream
    """

    def run(chan: Channel):
        chan.play()


class Skip(ChannelAction):
    """
    action for skipping currently playing
    """

    def __init__(self, amount) -> None:
        super(self, {amount})

    def run(chan: Channel):
        chan.skip()
