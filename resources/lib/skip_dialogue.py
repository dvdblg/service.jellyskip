import xbmcgui, xbmc

OK_BUTTON = 201
NEW_BUTTON = 202
DISABLE_BUTTON = 210
ACTION_PREVIOUS_MENU = 10
ACTION_BACK = 92
INSTRUCTION_LABEL = 203
AUTHCODE_LABEL = 204
WARNING_LABEL = 205
CENTER_Y = 6
CENTER_X = 2


class CustomDialog(xbmcgui.WindowXMLDialog):

    def __init__(self, xmlFile, resourcePath, seek_time_seconds, segment_type):
        self.seek_time_seconds = seek_time_seconds
        self.segment_type = segment_type

    def onInit(self):
        skip_label = 'Skip ' + str(self.segment_type)
        skip_button = self.getControl(OK_BUTTON)
        skip_button.setLabel(skip_label)

    def onAction(self, action):
        if action == ACTION_PREVIOUS_MENU or action == ACTION_BACK:
            self.close()

    def onControl(self, control):
        pass

    def onFocus(self, control):
        pass

    def onClick(self, control):
        player = xbmc.Player()

        if not player.isPlaying():
            self.close()
            return

        if control == OK_BUTTON:
            player.seekTime(self.seek_time_seconds)

        if control in [OK_BUTTON, NEW_BUTTON, DISABLE_BUTTON]:
            self.close()