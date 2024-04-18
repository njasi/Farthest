import logging

logger = logging.getLogger(__name__)


class VideoStreamer:
    """
    A wrapper around some tech for streaming farther video
    """

    def __init__(
        self,
        host="localhost",
        port=8080,
        get_next=None,
        peek=None,
        default_screen="./downloaded/empty.mp4",
    ):
        # where to stream to
        self.port = port
        self.host = host

        # player state management
        self.empty = False
        self.playing = False

        # interact with the manager:
        #   - remove from queue
        #   - check the front video
        self.get_next = get_next
        self.peek = peek

        # default animation
        self.default_screen = default_screen

    def stream(self, event=None) -> None:
        """
        Play the next video in the channel queue

        if the queue is empty (ie get_next returns None)
        then we start looping the default screen.
        """
        try:
            # TODO implement
            pass
        except Exception as e:
            logger.error(e)

    def get_progress(self) -> int:
        """
        Get the number of seconds into the current video
        return 0 if empty, maybe raise an error instead?
        """
        if self.empty:
            return 0

        # TODO implement
        return 0

    def get_length(self) -> int:
        """
        Return  the number of seconds in the current video
        return None if empty, maybe raise an error instead?
        """
        if self.empty:
            return 0

        # TODO implement
        return 0

    def get_remaining(self) -> int:
        """
        Return  the number of seconds left in the current video
        return None if empty, maybe raise an error instead?
        """
        if self.empty:
            return 0

        return int(self.get_length() - self.get_progress())

    def time_set(self, time):
        """
        Set the current time to the given time (seconds),
        allows skipping back or forward
        """
        if time < 0:
            time = 0
        elif time > self.get_length():
            time = self.get_length()

        # TODO implement
        # self.player.set_time(time * 1000)

    def time_add(self, amount):
        """
        Set time helper
        """
        self.time_set(self.get_progress() + amount)

    def skip(self):
        """
        Stop the currently playing item, and play the next one.
          - Don't allow when playing the default screen.
        """
        if self.empty:
            return False

        # TODO implement

    def is_playing(self):
        """
        return if the video is cuurrently playing
        """
        return self.playing

    def pause(self):
        """
        Pause the currently playing item
          - Don't allow when playing the default screen.
        """
        # set the state
        self.playing = False

        if self.empty or not self.is_playing():
            return False

        # TODO implement
        return True

    def play(self):
        """
        Play the currently playing item
          - Don't allow when playing the default screen.
        """
        # set the state
        self.playing = True

        if self.empty or self.is_playing():
            return False

        # TODO implement
        return True

    def kill(self):
        """Kill the stream & release any resources"""
        # TODO implement


    def volume(self):
        """
        volume is meant to be controllable at the client
        but maybe we can control it here too,
        like make all clients quieter
        """
        # TODO

    def play_ad(self):
        """
        function to play an ad
            - pause the current stream
            - play an ad for its duration
            - resume the stream
        """
        # TODO

    def set_playback_speed(self):
        """
        set the playback speed of the stream

        possible feature but idk if its good idea
        """
        # TODO
