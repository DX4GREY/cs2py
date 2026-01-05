import globals
from functions import memfuncs

from features import aimbot
from features import combined

from features import rcs
from features import esp
from features import bombtimer
from features import fovchanger
from features import bhop
from features import discodrpc
from features.spectlist import SpectatorList

from GUI import gui_mainloop
from GUI import gui_util

import multiprocessing
import threading, time

import win32con, win32process, win32api
import keyboard, os, json

keyboard.add_hotkey("end", callback=lambda: os._exit(0))
keyboard.add_hotkey("insert", callback=lambda: gui_util.hide_dpg())
keyboard.add_hotkey("home", callback=lambda: gui_util.streamproof_toggle())

class ManagedConfig:
	def __init__(self, managed_dict, save_function):
		self._dict = managed_dict
		self._save_function = save_function

	def update(self, *args, **kwargs):
		self._dict.update(*args, **kwargs)
		self._save_function(self._dict)

	def __setitem__(self, key, value):
		self._dict[key] = value
		self._save_function(self._dict)

	def __getitem__(self, key):
		return self._dict[key]

	def __delitem__(self, key):
		del self._dict[key]
		self._save_function(self._dict)

	def __contains__(self, key):
		return key in self._dict

	def get(self, key, default=None):
		return self._dict.get(key, default)

	def items(self):
		return self._dict.items()

	def keys(self):
		return self._dict.keys()

	def values(self):
		return self._dict.values()

	def __repr__(self):
		return repr(self._dict)
	
def SaveConfig(options):
	os.makedirs(os.path.dirname(globals.SAVE_FILE), exist_ok=True)
	with open(globals.SAVE_FILE, 'w') as fp:
		json.dump(dict(options), fp, indent=4)

def LoadConfig():
	os.makedirs(os.path.dirname(globals.SAVE_FILE), exist_ok=True)
	if not os.path.exists(globals.SAVE_FILE):
		with open(globals.SAVE_FILE, "w") as fp:
			json.dump(globals.CHEAT_SETTINGS, fp, indent=4)
	else:
		with open(globals.SAVE_FILE, "r") as fp:
			globals.CHEAT_SETTINGS = json.load(fp)

if __name__ == "__main__":
	win32process.SetPriorityClass(win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, win32api.GetCurrentProcessId()), win32process.HIGH_PRIORITY_CLASS)
	multiprocessing.freeze_support()
	ARDUINO_HANDLE = None
	timeout = 120.0
	start_time = time.time()

	ProcessObject = None
	print("Waiting for cs2.exe...")
	while time.time() - start_time < timeout:
		try:
			ProcessObject = memfuncs.GetProcess("cs2.exe")
		except Exception:
			ProcessObject = None
		if ProcessObject:
			break
		time.sleep(0.5)
	if not ProcessObject:
		print("Timeout: cs2.exe not found within 60s")
		os._exit(1)
	ClientModuleAddress = None
	print("Waiting for module handle...")
	while time.time() - start_time < timeout:
		try:
			ClientModuleAddress = memfuncs.GetModuleBase(modulename="client.dll", process_object=ProcessObject)
		except Exception:
			ClientModuleAddress = None
		if ClientModuleAddress:
			break
		time.sleep(0.5)
	if not ClientModuleAddress:
		print("Timeout: client.dll not found within 60s")
		os._exit(1)

	LoadConfig()

	Manager = multiprocessing.Manager()
	SharedOptions_M = Manager.dict(globals.CHEAT_SETTINGS)
	SharedOptions = ManagedConfig(SharedOptions_M, save_function=SaveConfig)

	SharedOffsets = Manager.Namespace()
	SharedOffsets.offset  = globals.GAME_OFFSETS

	GUI_proc = multiprocessing.Process(target=gui_mainloop.run_gui, args=(SharedOptions,))
	GUI_proc.start()

	esp.pme.overlay_init(title="ESP-Overlay")
	fps = esp.pme.get_monitor_refresh_rate()
	esp.pme.set_fps(fps)
	width, height = esp.pme.get_screen_width(), esp.pme.get_screen_height()

	FOV_proc = multiprocessing.Process(target=fovchanger.FovChangerThreadFunction, args=(SharedOptions, SharedOffsets,))
	FOV_proc.start()

	SharedBombState = Manager.Namespace()
	SharedBombState.bombPlanted = False
	SharedBombState.bombTimeLeft = -1
	Bomb_proc = multiprocessing.Process(target=bombtimer.BombTimerThread, args=(SharedBombState, SharedOffsets,))
	Bomb_proc.daemon = True
	Bomb_proc.start()

	discord_rpc_proc = multiprocessing.Process(target=discodrpc.DiscordRpcThread, args=(SharedOptions, ))
	discord_rpc_proc.daemon = True
	discord_rpc_proc.start()

	SharedSpectatorList = SpectatorList()

	while esp.pme.overlay_loop():
		esp.ESP_Update(ProcessObject, ClientModuleAddress, SharedOptions, SharedOffsets, SharedBombState, SharedSpectatorList)

		if SharedOptions["EnableAimbot"] and win32api.GetAsyncKeyState(SharedOptions["AimbotKey"]) & 0x8000:
			aimbot.Aimbot_Update(ProcessObject, ClientModuleAddress, SharedOffsets, SharedOptions, ARDUINO_HANDLE=ARDUINO_HANDLE)

		if SharedOptions["EnableBhop"]:
			bhop.Bhop_Update(ProcessObject, ClientModuleAddress, SharedOffsets)

		combined.Triggerbot_AntiFlash_Update(ProcessObject, ClientModuleAddress, SharedOffsets, SharedOptions)
		rcs.RecoilControl_Update(ProcessObject, ClientModuleAddress, SharedOffsets, SharedOptions, ARDUINO_HANDLE=ARDUINO_HANDLE)