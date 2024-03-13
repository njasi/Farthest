import vlc
import time


class StreamPlayer:
    """
    Basic class to manage the vlc instance
    """

    def __init__(self, stream_url: str):
        # make the vlc instance and player
        self.instance = vlc.Instance("--quiet")
        self.player = self.instance.media_player_new("--I macosx")

        # connect to stream
        self.connect(stream_url)


        self._window_macosx()

        # make the window (?)
        # self.player.set_fullscreen(True)
        # self.player.video_set_mouse_input(False)
        # self.player.video_set_key_input(False)

    def _window_macosx(self):
        """
        attach the window to vlc for macosx
        for some reason the normal media player doesnt make an interface regardless of argument

        so we get some os specific thing here to give it a place to play
        """
        from PySide6 import QtWidgets, QtGui

        # avGeom = QtGui.QDesktopWidget().availableGeometry()
        # avGeom.setTop(24)


        vlcApp = QtWidgets.QApplication([])
        vlcWidget = QtWidgets.QFrame()
        vlcWidget.resize(1080,720)
        vlcWidget.show()

        vlcWidget.setWindowTitle("Farther Python Client")
        vlcWidget.showMaximized()
        # vlcWidget.setGeometry(avGeom)

        self.player.set_nsobject(vlcWidget.winId())

        # player.play()

        vlcApp.exec()

    def connect(self, stream_url: str):
        """
        Connect to a new stream

        streal_url:     str, the addr of the stream
        """
        self.stream_url = stream_url

        # make new media for it and then set it
        self.media = self.instance.media_new(stream_url)
        self.media.get_mrl()
        self.player.set_media(self.media)
        self.play()

    def reload(self):
        """
        Just reload the stream by reconnecting
        """
        self.connect(self.stream_url)

    def play(self):
        self.player.play()

    def pause(self):
        self.player.stop()

    def sync(self):
        """
        sync up with the stream
        """
        # TODO not sure exactly what format will be used

    def set_volume(self, volume):
        """
        Set the volume of the player, r
        """
        if 0 <= volume <= 100:
            self.player.audio_set_volume(volume)
        # todo raise error maybe


if __name__ == "__main__":
    player = StreamPlayer("http://192.168.0.11:1234")
