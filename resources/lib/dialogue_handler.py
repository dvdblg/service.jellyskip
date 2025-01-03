import xbmc, xbmcaddon
import helper.utils as utils

from skip_dialogue import CustomDialog
from jellyfin.jellyfin_grabber import JellyfinHack
from skip_dialogue import CustomDialog
from helper import LazyLogger

addonInfo = xbmcaddon.Addon().getAddonInfo
addonPath = utils.translate_path(addonInfo('path'))

LOG = LazyLogger(__name__)

SECOND_PADDING = 1


class DialogueHandler:

    def __init__(self):
        self.dialogue = None
        self.scheduled_thread = None
        self.last_item = None

    def cancel_scheduled(self):
        if self.scheduled_thread:
            self.scheduled_thread.cancel()
            self.scheduled_thread = None
            LOG.info("Cancelled existing scheduled dialogue")

    def schedule_skip_gui(self, item, current_seconds):
        if not item:
            return

        # Cancel any existing scheduled thread
        self.cancel_scheduled()

        if item.get_start_seconds() < current_seconds:
            self.open_gui(item)
        else:
            seconds_till_start = item.get_start_seconds() - current_seconds
            self.scheduled_thread = utils.run_threaded(self.on_gui_scheduled, delay=seconds_till_start + SECOND_PADDING,
                                                       kwargs={'item': item})
            LOG.info(
                f"Scheduled dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()} in {seconds_till_start} seconds")

    def on_gui_scheduled(self, item):
        self.scheduled = item

        player = xbmc.Player()
        current_seconds = player.getTime()

        LOG.info(
            f"Opening scheduled dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()} as we are within the segment")
        if item.get_start_seconds() <= current_seconds <= item.get_end_seconds() - SECOND_PADDING:
            self.open_gui(item)
        else:
            # We are not within the segment
            LOG.info(
                f"Skipping dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()} as we are not within the segment")
            return

    def close_gui(self):
        if self.dialogue:
            self.dialogue.close()
            self.dialogue = None

    def is_last_item(self, item):
        if not self.last_item or not item:
            return False

        same_item_id = item.item_id == self.last_item.item_id
        same_type = item.segment_type== self.last_item.segment_type
        same_start = item.get_start_seconds() == self.last_item.get_start_seconds()
        same_end = item.get_end_seconds() == self.last_item.get_end_seconds()

        return same_item_id and same_type and same_start and same_end

    def open_gui(self, item):
        if self.is_last_item(item):
            LOG.info(f"Skipping dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()} as it is the same as the last item")
            return

        self.last_item = item
        LOG.info(f"Opening dialogue for {item.get_segment_type_display()} at {item.get_start_seconds()}")
        self.close_gui()
        dialog = CustomDialog('script-dialog.xml', addonPath, seek_time_seconds=item.get_end_seconds(),
                              segment_type=item.get_segment_type_display())
        self.dialogue = dialog
        dialog.doModal()
        del dialog


dialogue_handler = DialogueHandler()
