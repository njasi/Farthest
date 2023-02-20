import vlc
import json
import yt_dlp
import datetime
import os
src = os.path.dirname(os.path.realpath(__file__))

# TODO figure out why this doesnt work
ydl_opts = {
    'quiet': True
}
youtube_dl_manager = yt_dlp.YoutubeDL(ydl_opts)


f = open(src + "/../config.json", "r")
config = json.load(f)
FARTHER_CHAT = config["farther_chat_id"]
FARTHER_CHANNEL = config["farther_channel_id"]
f.close()


TYPE_YOUTUBE = "YOUTUBE"
# ik the raw file adds security issues, but its funny
TYPE_RAW = "RAW"

class AudioValue:
    def __init__(self, url, image, title, added, length, user_id):
        self.url = url
        self.image = image
        self.title = title
        self.added = added
        self.length = length
        self.user_id = user_id
        self.type = TYPE_YOUTUBE

    def get_audio_url(self):
        if self.type == TYPE_YOUTUBE:
            print("[YOUTUBE]:\tFinding audio url.")
            ydl_opts = {
                'format': 'worstaudio/worst',
                'keepvideo': False,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_info = ydl.extract_info(
                    url=self.url,
                    download=False
                )

                url = None
                for format in video_info["formats"]:
                    if format["audio_ext"] != "none" and \
                            (not url or "audio only" in format["format"]):
                        url = format["url"]
                        break
                print(f"[YOUTUBE]\t\tFound : {url}")
                return url
        elif self.type == TYPE_RAW:
            print(f"[RAW]:\t\tPlaying {self.url}")
            return self.url
        return None

    def to_html(self, current=False):
        str = f"<b><a href='{self.url}'>{self.title}</a></b>"
        if current:
            str += f" ({datetime.timedelta(seconds=int(current))}/{datetime.timedelta(seconds=self.length)})"
            return str
        return str + f" ({datetime.timedelta(seconds=self.length)})"

    def send(self, bot, now=False, wait=0):
        try:
            text = ""
            if now:
                text = f"<b>Playing 'song':</b>\n{self.to_html()}\nAdded by: <a href = 'tg://user?id={self.user_id}'>{self.added}</a>"
            else:
                text = f"<b>Added 'song':</b>\n{self.to_html()}\n\tAdded by: <a href = 'tg://user?id={self.user_id}'>{self.added}</a>\n Plays in {datetime.timedelta(seconds=wait)}"

            bot.send_message(chat_id=FARTHER_CHAT,
                             text=text, parse_mode="HTML")
            if now:
                bot.send_message(chat_id=FARTHER_CHANNEL,
                                 text=text, parse_mode="HTML")
        except:
            pass


class AudioQueue:
    def __init__(self, bot):
        self.queue = []
        self.vlc = vlc.Instance()
        self.player = self.vlc.media_player_new()
        self.paused = False
        self.bot = bot
        self.volume = 20
        self.currently_playing = None

    def get_length(self):
        total = 0
        if self.currently_playing == None:
            return 0
        total = self.currently_playing.length - \
            int(self.player.get_time() / 1000)
        for item in self.queue:
            total += item.length
        return total

    def play_next(self, event=None):
        if self.queue == []:
            # queue is empty
            self.currently_playing = None
            self.bot.send_message(
                text="The queue is now empty. use /add to add things.", chat_id=FARTHER_CHAT)
            return

        next = self.queue.pop(0)
        next.send(self.bot, now=True)

        # TODO: fix below
        # there has to be a better way to do this but when
        # I made only one player it refused to play another
        # bit of audio after the first, so here we are...
        self.player = self.vlc.media_player_new()
        vlc.libvlc_audio_set_volume(self.player, self.volume)
        self.player.event_manager().event_attach(
            vlc.EventType.MediaPlayerEndReached, self.play_next)
        self.player.event_manager().event_attach(
            vlc.EventType.MediaPlayerEncounteredError, self.play_next)

        # play the next audio
        url = next.get_audio_url()
        if url == None:
            self.bot.send_message(
                chat_id=FARTHER_CHAT,
                text="Farthest was unable to find a suitable audio file for this video. Perhaps try a different link for the same song.", parse_mode="HTML")
            self.currently_playing = next
            self.play_next()
            return
        media = self.vlc.media_new(url)
        self.player.set_media(media)
        self.player.play()
        self.currently_playing = next

    def add_audio(self, audio: AudioValue):
        if not self.currently_playing == None:
            audio.send(self.bot, None, self.get_length())
        self.queue.append(audio)
        if self.currently_playing == None:
            self.play_next()

    def pause(self):
        self.paused = True
        self.player.pause()

    def play(self):
        self.paused = False
        self.player.play()
        pass

    def skip(self):
        self.player.stop()
        skipped = self.currently_playing
        if skipped != None:
            self.play_next()
        return skipped

    def remove(self, index):
        # remove object from queue at index
        try:
            self.queue.pop(index)
            return True
        except:
            return False

    def queue_to_string(self):
        list = f"<b> Queue ({datetime.timedelta(seconds=self.get_length())}): </b>\n"
        if not self.currently_playing:
            list += "\tempty, use /add to add things to the list"
            return list

        list += "\t[1] " + \
            self.currently_playing.to_html(self.player.get_time()/1000) + "\n"
        i = 1
        for item in self.queue:
            if i > 9:
                break
            list += f"\t[{i+1}] " + item.to_html() + "\n"
            i += 1
        return list

    def set_volume(self, level):
        vlc.libvlc_audio_set_volume(self.player, level)
        self.volume = level
        pass
