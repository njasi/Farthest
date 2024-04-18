import vlc
import logging
import os

logger = logging.getLogger(__name__)

# NOTE: depreciated, dont use unless u update it to the new VideoStreamer class standards

class VlcStreamer:
    """
    A wrapper around vlc for streaming video

    should be easy to swap out for another streaming method if
    you implement all of the functions to do the same thing
    I dont believe any of the code refrences stuf other than the
    functions (and .empty)
    """

    def __init__(self, host="localhost", port=8080, dequeue=None, get_playlist=None):
        self.port = port
        # TODO inspect the quality of the stream with these options
        # f":sout=#transcode{{vcodec=h264,acodec=mp3,ab=128,channels=2,samplerate=44100}}:std{{access=http,mux=ts,dst=:{port}}}"
        # f":sout=#transcode{{vcodec=h264,acodec=mp3,ab=128,channels=2,samplerate=44100}}:std{{access=http,mux=ts,dst=:{port}}}"
        # f":sout=#transcode{{vcodec=h264,ab=128,channels=2,samplerate=44100}}:rtp{{dst=:{port}}}"
        self.options = (
            # f":sout=#transcode{{vcodec=h264,ab=128,channels=2,samplerate=44100}}"
            f":sout=#transcode{{vcodec=h264,acodec=mpga,vb=2000,ab=128,venc=x264{{preset=ultrafast,tune=zerolatency}}}}"
            # f":rtp{{access=udp,mux=ts,dst={host},port={port},sdp=sap,sap,name='Farther Stream'}}"
            # f":rtp{{access=udp,mux=ts,dst={host},port={port}}}"
            # f":rtp{{mux=ts,dst={host},sdp=sap,name='TestStream'}}"
            f":std{{access=http,mux=ts,dst=:{port}}}"
        )

        logger.info(f"Streamer options: {self.options}")

        # suppress vlc logging https://github.com/oaubert/python-vlc/issues/119
        # os.environ["VLC_VERBOSE"] = str("-1")

        # these manage the currently playing video, get_next is passed from the related channelmanager
        self.empty = False
        self.dequeue = dequeue
        self.get_playlist = get_playlist

        # default animation
        self.default_screen = "./downloaded/empty.mp4"

        # vlc instance setup
        self.vlc = vlc.Instance("--no-xlib")

        # load in playlist before oading player
        self.playlist = self.vlc.media_list_new()
        self.update_playlist()

        self.player = self.vlc.media_list_player_new()
        self.player.set_media_list(self.playlist)

        self._attach_events()

    def update_playlist(self, skip_current=False):
        """
        Update the vlc media_list instance

        - compare db queue with the media playlist
            - if mrl does not match then replace
            - if playlist is longer than db, truncate it
        - maintain the last element as the default video
        """

        logger.info("Updating the playlist")

        pl = self.get_playlist()
        pc = self.playlist.count()

        # we dont want anything else touching the list in the middle of this
        self.playlist.lock()

        for i, item in enumerate(pl):
            if i >= pc:
                # if we're past the playlist we want to be adding now
                self.playlist.insert_media(self._new_media(item), i)
                continue

            curr = self.playlist.item_at_index(i)

            if not curr.get_mrl() == self._get_mrl(item):
                # mrl is different, we should replace it
                # even if the same video, the mrl has updated so
                # we shoud change it out
                self.playlist.remove_index(i)
                self.playlist.insert_media(self._new_media(item), i)

        # remove any extras
        if len(pl) < pc:
            for i in range(len(pl), pc):
                self.playlist.remove_index(i)

        # add the default screen at the very end
        pc = self.playlist.count()
        self.playlist.insert_media(self._new_media(None, mrl=self.default_screen), pc)
        self.playlist.unlock()

        # if the list was empty before adding the default screen
        self.empty = pc == 0

    def _get_mrl(self, video):
        """
        Get the preferred resource from the video
        """

        return video.download_path if video.downloaded else video.resource_url

    def _new_media(self, video, mrl=None):
        """
        make a new media instance with the custom
        video.id metadata attached

        video:  any, the related db video entry
        """
        media = None
        if mrl is not None:
            media = self.vlc.media_new(mrl)
        else:
            media = self.vlc.media_new(self._get_mrl(video))
            # media.set_meta("title", video.title)
            # media.save_meta("title")
        media.add_option(self.options)
        return media

    def _playlist_str(self):
        res = []

        self.playlist.lock()
        for i in range(self.playlist.count()):

            curr = self.playlist.item_at_index(i)

            # title = curr.get_meta(self, "title")

            res += [f"[{i}] {1}"]

    def _attach_events(self):
        """
        Attach events to the vlc player that do the following:

            on video end or error, play the next one
            TODO test if this actually works
            last time the callbacks would die after one go
        """
        self.player.event_manager().event_attach(
            vlc.EventType.MediaPlayerEncounteredError,
            lambda e: logger.error("streamer error:", e),
        )

        # self.player.event_manager().event_attach(
        #     vlc.EventType.MediaPlayerEndReached, self.dequeue
        # )
        def handleNext(event):
            logger.info("Dequeueing front & updating playlist")
            self.dequeue()
            self.update_playlist()

        self.player.event_manager().event_attach(
            vlc.EventType.MediaListPlayerNextItemSet,
            handleNext,
        )
        # self.player.event_manager().event_attach(
        #     vlc.EventType.MediaPlayerEncounteredError, self.stream
        # )

    def stream(self, event=None) -> None:
        """
        Play the next video in the channel queue

        if the queue is empty (ie get_next returns None)
        then we start looping the default screen.
        """
        try:
            # update the playlist & start playing it
            self.update_playlist()
            self.player.play()

        except Exception as e:
            logger.error(e)

    def get_progress(self) -> int:
        """
        Get the number of seconds into the current video
        return 0 if empty, maybe raise an error instead?
        """
        if self.empty:
            return 0

        return int(self.player.get_media_player().get_time() / 1000)

    def get_remaining(self) -> int:
        """
        Return  the number of seconds left in the current video
        return None if empty, maybe raise an error instead?
        """
        if self.empty:
            return 0

        return int(
            (self.player.get_media_player().get_length() - self.get_progress()) / 1000
        )

    def kill(self):
        """Kill the stream & release the vlc resources"""
        self.playlist.release()
        self.player.release()
        self.vlc.release()

    def skip(self):
        """
        Stop the currently playing item, and play the next one.
          - Don't allow when playing the default screen.

        TODO: check if stopping the vid from the outside triggers the callback
        """

        # self.player.stop()

        # grab the next from the playlist & then update the playlist
        # since updating the playlist grabs from the db, this should
        # have the element removed
        self.player.next()
        self.update_playlist()

        # TODO do we need this still
        # self.stream()

    def pause(self):
        """
        Pause the currently playing item
          - Don't allow when playing the default screen.
        """
        if self.empty or not self.player.is_playing():
            return False
        self.player.pause()
        return True

    def play(self):
        """
        Play the currently playing item
          - Don't allow when playing the default screen.
        """
        if self.empty or self.player.is_playing():
            return False
        self.player.play()
        return True

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
