"""
A VideoStreamer which uses aiortc to stream with webrtc

- minimal delay ( < 1 second )
- uses FartherPlayer.py to control the tracks

"""

import json
import asyncio
import logging

logger = logging.getLogger(__name__)

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.rtcrtpsender import RTCRtpSender
from aiortc.contrib.media import MediaRelay, MediaBlackhole

from .FartherPlayer import FartherPlayer
from .VideoStreamer import VideoStreamer


class AiortcStreamer(VideoStreamer):
    """
    A wrapper around aiortc for streaming farther video & audio
    """

    def __init__(
        self,
        host="localhost",
        port=8080,
        get_next=None,
        peek=None,
        default_screen="./downloaded/empty.mp4",
    ):
        super().__init__(host, port, get_next, peek, default_screen)

        self.player = FartherPlayer(
            self.default_screen, decode=True, finish_callback=self._stream_next
        )
        self._relay = MediaRelay()

        # i imagine we keep the stream running by having this subscribed
        # to the relay (or however that works)
        self._blackhole = MediaBlackhole()
        self.pcs = set()

        # TODO look through webcam.py and figure out what we need

    def _get_tracks(self):
        """
        get farther audio + video tracks by subscribing to the relay
        """

        return self._relay.subscribe(self.player.audio), self._relay.subscribe(
            self.player.video
        )

    async def _offer(self, request):
        params = await request.json()
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

        pc = RTCPeerConnection()
        self.pcs.add(pc)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print("Connection state is %s" % pc.connectionState)
            if pc.connectionState == "failed":
                await pc.close()
                self.pcs.discard(pc)

        # grab the media source
        audio, video = self._get_tracks()

        if audio:
            audio_sender = pc.addTrack(audio)
        if video:
            video_sender = pc.addTrack(video)

        await pc.setRemoteDescription(offer)

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
            ),
        )

    def _launch(self):
        """
        Start up the player, probably feed it into a mediasink or smth
        """
        # TODO

    def _stream_next(self):
        """
        grab the next song from the queue & stream it
        """

        next = self.get_next()
        self.stream(media=next)

    def stream(self, event=None, media=None) -> None:
        """
        Play the next video in the channel queue

        if the queue is empty (ie peek returns None)
        then we start looping the default screen.
        """
        try:
            if not media:
                media = self.peek()
            if media is None:
                # loop the default content if there is no video to play
                self.player.set_file(self.default_screen, decode=True, loop=True)
                return

            self.player.set_file(media.get_resource(), decode=True)

        except Exception as e:
            logger.error(e)

    def get_progress(self) -> int:
        """
        Get the number of seconds into the current video
        return 0 if empty, maybe raise an error instead?
        """
        if self.empty:
            return 0

        return self.player.time

    def get_length(self) -> int:
        """
        Return the number of seconds in the current video
        return None if empty, maybe raise an error instead?
        """
        if self.empty:
            return 0

        return self.player.duration

    def time_set(self, time):
        """
        Set the current time to the given time (seconds),
        allows skipping back or forward
        """
        if time < 0:
            time = 0
        elif time > self.get_length():
            time = self.get_length()

        self.player.seek(time)


    def kill(self):
        """Kill the stream & release any resources"""
        self.player.stop()

    def skip(self):
        """
        Stop the currently playing item, and play the next one.
          - note that the manager will handle dequeuing things for
            us, thus i imagine streamers will all just call their
            stream method
        """
        if self.empty:
            return False

        # TODO check how this work
        self.stream(None)

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

        if self.empty or not self.is_playing():
            return False

        self.player.pause()
        self.playing = False
        return True

    def play(self):
        """
        Play the currently playing item
          - Don't allow when playing the default screen.
        """
        # set the state

        if self.empty or self.is_playing():
            return False

        self.player.play()
        self.playing = True
        return True

    async def kill(self):
        # close peer connections
        coros = [pc.close() for pc in self.pcs]
        await asyncio.gather(*coros)
        self.pcs.clear()
