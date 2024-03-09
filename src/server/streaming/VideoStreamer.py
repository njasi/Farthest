import vlc


class VideoStreamer:
    def __init__(
        self,
        host="localhost",
        port=8080,
        get_next=None,
    ):
        self.port = port
        # TODO inspect the quality of the stream with these options
        self.options = f":sout=#transcode{{vcodec=h264,acodec=mp3,ab=128,channels=2,samplerate=44100}}:std{{access=http,mux=ts,dst=:{port}}}"

        self.vlc = vlc.Instance("--no-xlib")
        self.player = self.vlc.media_player_new()
        self.default_screen = "default.png"

        self.empty = True

        self.get_next = get_next

        # on video end or error, play the next one
        # TODO test if this actually works
        #   last time the callbacks would die after one go
        self.player.event_manager()
        self.player.event_manager().event_attach(
            vlc.EventType.MediaPlayerEndReached, self.stream
        )
        self.player.event_manager().event_attach(
            vlc.EventType.MediaPlayerEncounteredError, self.stream
        )

    def stream(self, event=None) -> None:
        """
        Play the next video in the channel queue

        if the queue is empty (ie get_next returns None)
        then we start looping the default screen.
        """
        # select the next video and play (becomes current)
        # telegram messages are handled in the Channel class
        # when the get_next cb is called
        current_video = self.get_next()
        ext_options = ""

        # If no next video display the default image instead
        resource = self.default_screen
        if current_video is None:
            self.empty = True
            ext_options = ":input-repeat=65535"
        else:
            self.empty = False
            # Load the video file, prefer path over url
            resource = (
                current_video.resource_path
                if current_video.resource_path
                else current_video.resource_url
            )

        media = self.vlc.media_new(resource)

        # put in our default options, ie
        # set up VLC to generate an HLS stream
        media.add_option(self.options)
        # will contain extra opts, ie it's the default screen, loop it
        media.add_option(ext_options)

        # add the media into the player & start playing it
        self.player.set_media(media)
        self.player.play()

    def get_progress(self) -> int:
        """
        Get the number of seconds into the current video
        return None if empty, maybe raise an error instead?
        """
        if self.empty:
            return None

        return int(self.player.get_time() / 1000)

    def get_remaining(self) -> int:
        """
        Return  the number of seconds left in the current video
        return None if empty, maybe raise an error instead?
        """
        if self.empty:
            return None

        self.player.get_length()

    def kill(self):
        """Kill the stream & release the vlc resources"""
        self.player.release()
        self.vlc.release()

    def skip(self):
        """
        Stop the currently playing item, and play the next one.
          - Don't allow when playing the default screen.

        TODO: check if stopping the vid from the outside triggers the callback
        """

        self.player.stop()
        self.player.remove()

        self.stream()

    def pause(self):
        """
        Pause the currently playing item
          - Don't allow when playing the default screen.
        """
        self.player.pause()

    def play(self):
        """
        Play the currently playing item
          - Don't allow when playing the default screen.
        """
        self.player.play()

    def set_time(self, time):
        """
        Set the current time to the given time (seconds),
        allows skipping back or forward
        """
        if time < 0:
            time = 0
        elif time > self.length:
            time = self.length

        self.player.set_time(time * 1000)

    def increment_time(self, amount):
        """
        Set time helper
        """
        self.get_progress() + amount

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
