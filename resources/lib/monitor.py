import xbmc, xbmcaddon

from helper import LazyLogger
import player
import helper.utils as utils

from jellyfin.jellyfin_grabber import JellyfinHack
from skip_dialogue import CustomDialog
from dialogue_handler import dialogue_handler

addonInfo = xbmcaddon.Addon().getAddonInfo
addonPath = utils.translate_path(addonInfo('path'))

jf_hack = JellyfinHack()

LOG = LazyLogger(__name__)


class JellySkipMonitor(xbmc.Monitor):


    def __init__(self):
        xbmc.Monitor.__init__(self)
        self.player = player.JellySkipPlayer(self)
        LOG.info('Init monitor')

    def start(self, **kwargs):
        LOG.info('Starting JellySkipMonitor')
        while not self.abortRequested():
            self.waitForAbort(1)

        self.stop()

    def _event_handler_player_change_playback(self, **_kwargs):
        LOG.info('JellySkipMonitor: player general event')
        self.start_tracking()

    def _event_handler_player_stop(self, **_kwargs):
        LOG.info('JellySkipMonitor: player stop event')
        jf_hack.reset_itemid()
        dialogue_handler.cancel_scheduled()
        LOG.info('JellySkipMonitor: reset itemid')

    def _event_handler_player_start(self, **_kwargs):
        LOG.info('JellySkipMonitor: player start event')
        jf_hack.reset_itemid()
        dialogue_handler.cancel_scheduled()

    EVENTS_MAP = {
        'Other.UserDataChanged': jf_hack.event_handler_jellyfin_userdatachanged,
        # 'Player.OnPause': _event_handler_player_change_playback,
        'Player.OnResume': _event_handler_player_change_playback,
        # 'Player.OnSpeedChanged': _event_handler_player_change_playback,
        'Player.OnSeek': _event_handler_player_change_playback,
        'Player.OnStop': _event_handler_player_stop,
        'Player.OnPlay': _event_handler_player_start,
        'Player.OnAVChange': _event_handler_player_change_playback,
    }

    def stop(self):
        LOG.info('Stopping JellySkipMonitor')

    def onNotification(self, sender, method, data=None):
        """Handler for Kodi events and data transfer from plugins"""

        sender = utils.from_bytes(sender)
        method = utils.from_bytes(method)
        data = utils.from_bytes(data) if data else ''

        handler = JellySkipMonitor.EVENTS_MAP.get(method)
        if not handler:
            return

        LOG.info(f"Notification: sender={sender}, method={method}, data={data}")

        handler(self, sender=sender, data=data)

        if method == 'Other.UserDataChanged':
            while not jf_hack.has_itemid():
                self.waitForAbort(1)

            LOG.info('JellySkipMonitor: getting media segments')

            if not self.player.isPlayingVideo() or not jf_hack.has_itemid():
                return

            jf_hack._fetch_media_segments()
            self.start_tracking()

    def start_tracking(self):
        if not self.player.isPlayingVideo():
            return

        time_seconds = self.player.getTime()
        duration_seconds = self.player.getTotalTime()

        media_segments = jf_hack.get_media_segments()

        # No media segments
        if not media_segments:
            return

        LOG.info(f"Start tracking: time={time_seconds}, duration={duration_seconds}")

        next_item = media_segments.get_next_item(time_seconds)

        if not next_item:
            return

        LOG.info(f"Next item: {next_item}")

        dialogue_handler.schedule_skip_gui(next_item, time_seconds)


