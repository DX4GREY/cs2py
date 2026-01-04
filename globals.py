import win32api
from ext import offsets
from ext.datatypes import *
import os

SCREEN_WIDTH = win32api.GetSystemMetrics(0)
SCREEN_HEIGHT = win32api.GetSystemMetrics(1)


GAME_OFFSETS = offsets.get_offsets()

SAVE_FILE = os.path.join("C:\\DHax", "settings.json")

CHEAT_SETTINGS = {
    "EnableAntiFlashbang": True,
    "EnableFovChanger": False,
    "FovChangeSize": 90,
    "EnableAimbot": True,
    "EnableAimbotPrediction": True,
    "EnableAimbotTeamCheck": True,
    "EnableAimbotVisibilityCheck": False,
    "AimbotFOV": 50,
    "AimbotSmoothing": 1,
    "AimPosition": "Neck",
    "AimbotKey": 17,
    "EnableRecoilControl": True,
    "RecoilControlSmoothing": 1.0,
    "EnableTriggerbot": False,
    "EnableTriggerbotKeyCheck": False,
    "TriggerbotKey": 17,
    "EnableTriggerbotTeamCheck": False,
    "EnableESPDistanceRendering": True,
    "EnableESPTeamCheck": True,
    "EnableESPSkeletonRendering": True,
    "EnableESPBoxRendering": False,
    "EnableESPTracerRendering": False,
    "EnableESPNameText": False,
    "EnableESPHealthBarRendering": True,
    "EnableESPHealthText": True,
    "EnableESPDistanceText": False,
    "EnableFOVCircle": False,
    "EnableESPBombTimer": False,
    "CT_color": "#000000",
    "T_color": "#FFFFFF",
    "FOV_color": "#FFFFFF",
    "EnableBhop": False,
    "EnableDiscordRPC": False,
    "EnableSpectatorList": False
}


RCS_CTRL_BY_AIMBOT = False