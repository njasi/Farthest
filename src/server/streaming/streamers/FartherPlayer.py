"""
Simple Player for aiortc based off of their MediaPlayer implementation

not a streamer, but the player that the AiortcStreamer will use

a lot of the code is just copy pasted from source and modified where neccessary
"""

import av
import cv2
import time
import errno
import asyncio
import logging
import threading
import fractions
import traceback
import numpy as np

from typing import Dict, Optional, Set, Union

from av import AudioFrame, VideoFrame
from av.audio import AudioStream
from av.frame import Frame
from av.packet import Packet
from av.video.stream import VideoStream

from aiortc.mediastreams import (
    AUDIO_PTIME,
    MediaStreamError,
    MediaStreamTrack,
    VideoStreamTrack,
    AudioStreamTrack,
)
from aiortc.contrib.media import PlayerStreamTrack, MediaPlayer, REAL_TIME_FORMATS

# NOTE: constants stolen from aiortc source
AUDIO_PTIME = 0.020  # 20ms audio packetization

# I think this is something inherent to the webrtc protocol (?), 9kHz clock rate
VIDEO_CLOCK_RATE = 90000
VIDEO_TIME_BASE = fractions.Fraction(1, VIDEO_CLOCK_RATE)


logger = logging.getLogger(__name__)


# NOTE: player_worker_decode & player_worker_demuux are mostly stolen from aiortc's mediapayer
#       didnt want to write custom stuff, but i neeed to change the throttle_playback section so
def player_worker_decode(
    loop,
    container,
    streams,
    audio_track,
    video_track,
    quit_event,
    throttle_playback,
    loop_playback,
    player,
):
    audio_sample_rate = 48000
    audio_samples = 0
    audio_time_base = fractions.Fraction(1, audio_sample_rate)
    audio_resampler = av.AudioResampler(
        format="s16",
        layout="stereo",
        rate=audio_sample_rate,
        frame_size=int(audio_sample_rate * AUDIO_PTIME),
    )

    video_first_pts = None

    frame_time = None

    while not quit_event.is_set():
        try:
            frame = next(container.decode(*streams))
        except Exception as exc:
            if isinstance(exc, av.FFmpegError) and exc.errno == errno.EAGAIN:
                time.sleep(0.01)
                continue
            if isinstance(exc, StopIteration) and loop_playback:
                container.seek(0)
                continue
            if audio_track:
                asyncio.run_coroutine_threadsafe(audio_track._queue.put(None), loop)
            if video_track:
                asyncio.run_coroutine_threadsafe(video_track._queue.put(None), loop)
            break

        # read up to 1 second ahead of the player
        if throttle_playback:
            player_time = player._time_a
            if video_track:
                player_time = player._time_v
            if player_time is None:
                player_time = 0

            if frame_time and frame_time > player_time + 1:
                time.sleep(0.1)

        if isinstance(frame, AudioFrame) and audio_track:
            for frame in audio_resampler.resample(frame):
                # fix timestamps
                frame.pts = audio_samples
                frame.time_base = audio_time_base
                audio_samples += frame.samples

                frame_time = frame.time
                asyncio.run_coroutine_threadsafe(audio_track._queue.put(frame), loop)
        elif isinstance(frame, VideoFrame) and video_track:
            if frame.pts is None:  # pragma: no cover
                logger.warning(
                    "MediaPlayer(%s) Skipping video frame with no pts", container.name
                )
                continue

            # video from a webcam doesn't start at pts 0, cancel out offset
            if video_first_pts is None:
                video_first_pts = frame.pts
            frame.pts -= video_first_pts

            frame_time = frame.time
            asyncio.run_coroutine_threadsafe(video_track._queue.put(frame), loop)


def player_worker_demux(
    loop,
    container,
    streams,
    audio_track,
    video_track,
    quit_event,
    throttle_playback,
    loop_playback,
    player,
):
    video_first_pts = None
    frame_time = None

    while not quit_event.is_set():
        try:
            packet = next(container.demux(*streams))
            if not packet.size:
                raise StopIteration
        except Exception as exc:
            if isinstance(exc, av.FFmpegError) and exc.errno == errno.EAGAIN:
                time.sleep(0.01)
                continue
            if isinstance(exc, StopIteration) and loop_playback:
                container.seek(0)
                continue
            if audio_track:
                asyncio.run_coroutine_threadsafe(audio_track._queue.put(None), loop)
            if video_track:
                asyncio.run_coroutine_threadsafe(video_track._queue.put(None), loop)
            break

        # read up to 1 second ahead of the player
        if throttle_playback:
            player_time = player._time_a
            if video_track:
                player_time = player._time_v
            if player_time is None:
                player_time = 0

            if frame_time and frame_time > player_time + 1:
                time.sleep(0.1)

        track = None
        if isinstance(packet.stream, AudioStream) and audio_track:
            track = audio_track
        elif isinstance(packet.stream, VideoStream) and video_track:
            if packet.pts is None:  # pragma: no cover
                logger.warning(
                    "MediaPlayer(%s) Skipping video packet with no pts", container.name
                )
                continue
            track = video_track

            # video from a webcam doesn't start at pts 0, cancel out offset
            if video_first_pts is None:
                video_first_pts = packet.pts
            packet.pts -= video_first_pts

        if (
            track is not None
            and packet.pts is not None
            and packet.time_base is not None
        ):
            frame_time = int(packet.pts * packet.time_base)
            asyncio.run_coroutine_threadsafe(track._queue.put(packet), loop)


class FartherPlayer(MediaPlayer):
    """
    An extension of the MediaPlayer class which manages the video & audio tracks

    most of the mediaplayer stuff is rewritten, just extending it for consistency
    - kinda had to rewrite cause so many things use __vars & mangling is annoying

    would have just used a MediaPlayer instance and manage it here but i needed
    to change the worker threads
    """

    # NOTE: the tracks will recieve a None from the player when the videos end

    def __init__(
        self,
        file,
        finish_cb,
        format=None,
        decode=True,
        options=None,
        timeout=None,
        loop=False,
    ) -> None:
        # TODO figure out how to deal with the tracks ending

        # basic state management
        self.playing = True
        self.empty = True  # TODO set empty = true on finish

        # call when media ends, idea is to queue the next media here
        # NOTE: when there are issues audio and video can get desynced for clients
        #       however audio is more important so we wait for the audio to finish
        #       before calling unless there isn't an audio track ofc
        self._finish_cb = finish_cb

        # track how long the player has been paused so we can resync the streams
        # (due to base MediaPlayer / PlayerStreamTrack timing)
        self._paused_time = None

        # worker thread stuff
        self.__thread: Optional[threading.Thread] = None
        self.__thread_quit: Optional[threading.Event] = None

        # av container (ffmpeg)
        self.__container = None

        # ready the output streams, they will send recv_empty until given a track, also
        # means we're good when switching tracks cause it can just show the empty frame
        self.__fvideo = FartherVideoTrack(None, self)
        self.__faudio = FartherAudioTrack(None, self)
        self.__audio: Optional[PlayerStreamTrack] = None
        self.__video: Optional[PlayerStreamTrack] = None

        # load the file,
        # NOTE: many instance vars are initialized in here
        self.set_file(
            file,
            format=format,
            decode=decode,
            options=options,
            timeout=timeout,
            loop=loop,
        )

    def set_file(
        self,
        file,
        format=None,
        decode=True,
        options=None,
        timeout=None,
        loop=False,
        seek=0,
    ):
        """
        Set the file to play, loads in a new media player instance after
        killing the old one (if there was an old one)

        - called @ start and when the video ends to change out to the new one
            - skips, removes, etc

        :param file:        The path to a file, or a file-like object.
        :param format:      The format to use, defaults to autodect.
        :param decode:      If the file needs to be decoded
        :param options:     Additional options to pass to FFmpeg.
        :param timeout:     Open/read timeout to pass to FFmpeg.
        :param loop:        Whether to repeat playback indefinitely (requires a seekable file).
        :param seek:        int, timestamp to seek to @start  (requires a seekable file duh)
        """

        # input args, save these for seeking
        self.file = file
        self.__format = format
        self.__decode = decode
        self.__options = options
        self.__timeout = timeout
        self.__seek = seek
        self.__loop_playback = loop

        # stop the streams (also gets their worker threads)
        # NOTE: these are the streams internal to the ftracks, not the actual
        #       tracks that the user sees
        if self.__audio is not None:
            self.__audio.stop()
            self.__audio = None
        if self.__video is not None:
            self.__video.stop()
            self.__video = None

        # clear the tracks
        self.__fvideo.set_track(None)
        self.__faudio.set_track(None)

        # reset the timing info
        self.fps = 30
        self.duration = 0
        self._time_v = None
        self._time_a = None

        # stuff stolen from the media player im just not gonna mess with
        self.__streams = []
        self.__started: Set[PlayerStreamTrack] = set()

        # load the file with av (ffmpeg wrapper) & seek to the requested timestamp
        if self.__container is not None:
            self.__container.close()
        self.__container = av.open(
            file=file, format=format, mode="r", options=options, timeout=timeout
        )
        self.__container.seek(seek * av.time_base)

        # calculate the duration, maybe check if av.time_base is always accurate
        self.duration = self.__container.duration / av.time_base

        # check if we need to throttle playback
        container_format = set(self.__container.format.name.split(","))
        self._throttle_playback = not container_format.intersection(REAL_TIME_FORMATS)

        # update the tracks & set the farther track values
        for stream in self.__container.streams:
            try:
                if stream.type == "audio" and not self.__audio:
                    if self.__decode or stream.codec_context.name in [
                        "opus",
                        "pcm_alaw",
                        "pcm_mulaw",
                    ]:
                        self.__audio = PlayerStreamTrack(self, kind="audio")
                        self.__faudio.set_track(self.__audio)

                        self.__streams.append(stream)

                elif stream.type == "video" and not self.__video:
                    # grab the fps from the vid stream
                    self.fps = stream.average_rate

                    if self.__decode or stream.codec_context.name in ["h264", "vp8"]:
                        self.__video = PlayerStreamTrack(self, kind="video")
                        self.__fvideo.set_track(self.__video)
                        self.__streams.append(stream)

            except Exception as e:
                traceback.print_exception(e)
                logger.error(f"FartherPlayer({self.__container.name}) {e}")

        # no longer empty
        self.empty = False

    ###################################
    # FartherPlayer control functions #
    ###################################

    def pause(self):
        self._paused_time = time.time()
        self.playing = False

        # remove the timestamps from the empty tracks so they reset their timing
        # functions & dont wait super long
        # This is pretty specific to the Base VideoStreamTrack & AudioStreamTrack,
        # but I dont think i'll be using anything else for now
        # also if it changes I imagine theyre gonna be custom made classes so u can fix it here lol
        try:
            delattr(self.__faudio._track_empty, "_timestamp")
            delattr(self.__fvideo._track_empty, "_timestamp")
        except:
            pass

    def play(self):

        # add to the start time so that the player tracks dont try
        # to go super fast to "keep up"

        if self._paused_time is not None:
            if self.__video is not None:
                self.__video._start += time.time() - self._paused_time
            if self.__audio is not None:
                self.__audio._start += time.time() - self._paused_time
            self._paused_time = None

        self.playing = True

        # could cheat by reseeking the moment lol
        # self.seek(int(self.time))

    def stop(self):
        """
        Clean up all the resources

            - stop both of the tracks worker threads
            - close the av container if exists
        """
        self.__fvideo.stop()
        self.__faudio.stop()
        if self.__container is not None:
            self.__container.close()

    def seek(self, timestamp):
        """
        Seek to the given timestamp (in seconds)
        """
        # easer to just reset the file with the new seek value lol
        #   (dont feel like communicating with worker threads)
        self.set_file(
            self.file,
            seek=timestamp,
            format=self.__format,
            decode=self.__decode,
            options=self.__options,
            timeout=self.__timeout,
            loop=self.__loop_playback,
        )

    def _finished_track(self, track):
        """
        For tracks to signal to the mediaplayer that
        they have finished playing

        NOTE: we assume that a track is done if:
            - it returns a None frame
            - or it raises MediaStreamError
        """

        logger.info(f"FartherPlayer finished {self.file} {track.kind}")
        track.set_track(None)

        if track.kind == "audio":
            self._finish_cb()

        # only do cb when video finishes if theres no audio track
        if track.kind == "video" and self.__audio is None:
            self._finish_cb()

    ##################################
    # Convenience property accessors #
    ##################################

    @property
    def time(self):
        """
        get the current playback timestamp

        NOTE: this is updated by the tracks in their recv functions
        """
        if self._time_v is None:
            if self._time_a is not None:
                return self.__seek
            return self.__seek + self._time_a
        return self.__seek + self._time_v

    @property
    def audio(self) -> MediaStreamTrack:
        """
        A :class:`aiortc.MediaStreamTrack` instance if the file contains audio.
        """
        return self.__faudio

    @property
    def video(self) -> MediaStreamTrack:
        """
        A :class:`aiortc.MediaStreamTrack` instance if the file contains video.
        """
        return self.__fvideo

    ###################################
    # Functions for use by the tracks #
    ###################################

    def _start(self, track: PlayerStreamTrack) -> None:
        self.__started.add(track)
        if self.__thread is None:
            self.__log_debug("Starting FartherPlayer worker thread")
            self.__thread_quit = threading.Event()
            self.__thread = threading.Thread(
                name="media-player",
                target=player_worker_decode if self.__decode else player_worker_demux,
                args=(
                    asyncio.get_event_loop(),
                    self.__container,
                    self.__streams,
                    self.__audio,
                    self.__video,
                    self.__thread_quit,
                    self._throttle_playback,
                    self.__loop_playback,
                    self,
                ),
            )
            self.__thread.start()

    def _stop(self, track: PlayerStreamTrack) -> None:
        self.__started.discard(track)

        if not self.__started and self.__thread is not None:
            self.__log_debug("Stopping worker thread")
            self.__thread_quit.set()
            self.__thread.join()
            self.__thread = None

        if not self.__started and self.__container is not None:
            self.__container.close()
            self.__container = None

    def __log_debug(self, msg: str, *args) -> None:
        logger.debug(f"FartherPlayer(%s) {msg}", self.__container.name, *args)


class FartherTrack:
    """
    Single track within farther player, manages the passed tracks
    """

    def __init__(self, track, player, empty) -> None:
        super().__init__()
        self._track = track
        self._track_empty = empty
        self._player = player
        self._prev = None

    @property
    def readyState(self):
        if self._track is None:
            return "live"
        return self._track.readyState

    def set_track(self, track):
        """
        Set the track that this instance is managing
        """
        self._track = track

    def stop(self):
        """stop the track"""
        self._track.stop()
        super().stop()

    async def _recv_base(self):
        """
        Grab the next chunk from the source track
        """
        frame = None
        try:
            frame = await self._track.recv()
        except MediaStreamError as e:
            # NOTE: this kind of error is raised when there's an error and
            # when the track comes to an end (see PlayerStreamTrack.recv)
            # In both situations it makes sense to tell the player that the
            # media is finished. (Farther wise => play next track)
            self._player._finished_track(self)
            raise e
        except Exception as e:
            # other errors should trigger the finished cb too
            self._player._finished_track(self)
            raise e

        if frame is None:
            # Otherwise if you're implementing a more reasonable track,
            # we assume a None frame means the track is done
            self._player._finished_track(self)

        return frame

    async def _recv_paused(self):
        """
        recv for when the stream is paused:
            - return the previous frame without requesting a new one
            - can be a slight desync when tracks start playing again (seems to be client based)

        NOTE: could also have a paused track (like ._track_empty), but i think just
              returning the last frame is fine
        """

        # steal timing from the empty track (lazy but ~works lol)
        await self._recv_empty()

        # return the prev frame
        return self._prev

    async def _recv_empty(self):
        """
        recv for when the stream is empty:
            - return silence for audio & a still frame for video

        TODO may make more sense to have the streamer
             manage this by adding the default video instead

        """
        return await self._track_empty.recv()

    async def _recv_error(self, error):
        """
        recv for when there is an error, default is just return the empty

        error:  the exception that occured
        """
        return await self._recv_empty()

    def _transform(self, frame):
        """
        transformation to apply to the frame from _recv_base
            - for video this might be overlaying some text or an ad.
            - not sure what would be useful for audio tbh
        """
        return frame

    async def recv(self):
        try:
            if self._player.empty or self._track is None:
                # if the streamer is empty, or the track is none
                # we return the empty frame for this track
                return await self._recv_empty()
            elif not self._player.playing:
                # if the streamer is not playing we return the paused frame
                # this way we dont consume frames from the mediaplayer
                return await self._recv_paused()

            # NOTE: PlayerStreamTrack controls the playback rate for us here
            #       assuming transform is quick at least lol
            base = await self._recv_base()
            next = self._transform(base)
            self._prev = next
            return next
        except Exception as e:
            traceback.print_exception(e)
            logger.error(f"FartherPlayer({self._player.file}) {e}")
            return await self._recv_error(e)


class FartherVideoTrack(FartherTrack):

    kind = "video"

    def __init__(self, track, player, empty=VideoStreamTrack()) -> None:
        super().__init__(track, player, empty)

    async def _recv_base(self):
        """
        Grab the next chunk from the source track & update player time
        """
        frame = await super()._recv_base()
        self._player._time_v = frame.time
        return frame

    def _transform(self, frame):
        """
        transformation to apply to the frame from _recv_base

        # NOTE: may want to resize video frames to a standard size, not
        #       necessary though, streaming works fine without it

        frame:      VideoFrame, the frame to transform
        """
        return frame

    def _darken(self, image, factor=0.5):
        """
        Darken the given image by multiplying each pixel value by a factor.

        could use smth like this for pauses, but probably better to talk
        to the client and tell it that its paused

        image:      numpy.ndarray, Input image.
        factor:     float, Factor to darken the image by.

        returns:    numpy.ndarray, Darkened image.
        """
        return np.clip(image * factor, 0, 255).astype(np.uint8)


class FartherAudioTrack(FartherTrack):

    kind = "audio"

    def __init__(self, track, player, empty=AudioStreamTrack()) -> None:
        super().__init__(track, player, empty)

    async def _recv_base(self):
        """
        Grab the next chunk from the source track & update player time
        """
        frame = await super()._recv_base()
        self._player._time_a = frame.time
        return frame

    async def _recv_paused(self):
        """
        recv for when the stream is paused:

        since this is audio we just wanna return silence...
        repeated last frame of audio would be horrible
        """

        return await self._recv_empty()
