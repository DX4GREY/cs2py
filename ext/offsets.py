from dataclasses import dataclass
import os
import json
import requests
import tempfile
import time

CS2_DUMPER_BASE_URL = "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output"
CS2_DUMPER_FILES = {
	"offsets": "offsets.json",
	"clientdll": "client_dll.json",
	"buttons": "buttons.json",
}
CACHE_MAX_AGE_SECONDS = 60 * 10

_OFFSETS_CACHE = None

@dataclass
class Offset:
	dwViewMatrix: int
	dwLocalPlayerPawn: int
	dwEntityList: int
	dwLocalPlayerController: int
	dwViewAngles: int
	dwGameRules: int
	dwSensitivity_sensitivity: int
	dwSensitivity: int 


	ButtonJump: int
	
	m_hPlayerPawn: int
	m_iHealth: int
	m_lifeState: int
	m_iTeamNum: int
	m_vOldOrigin: int
	m_pGameSceneNode: int
	m_modelState: int
	m_boneArray: int
	m_nodeToWorld: int
	m_sSanitizedPlayerName: int
	m_iIDEntIndex: int
	m_flFlashMaxAlpha: int
	m_fFlags: int
	m_iFOV: int
	m_pCameraServices: int
	m_bIsScoped: int

	m_vecViewOffset: int
	m_entitySpottedState: int 
	m_bSpotted: int 
	m_bBombPlanted: int
	
	m_iShotsFired: int
	m_aimPunchAngle: int
	
	m_bSpottedByMask: int
	m_vecVelocity: int

	m_hPawn: int
	m_pObserverServices: int
	m_hObserverTarget: int
	m_iszPlayerName: int
	m_iObserverMode: int

class Client:
	def __init__(self, manual_dump=False):
		self._cache_dir = self._get_cache_dir()
		self._meta_file = os.path.join(self._cache_dir, "meta.json")
		try:
			if not manual_dump:
				self._load_auto()
			else:
				self._load_from_file()
		except Exception as e:
			print(f"Unable to initialize offsets: {e}")
			exit()

	def _get_cache_dir(self):
		# Keep cached dumper files inside project output directory for offline fallback.
		root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
		cache_dir = os.path.join(root_path, "output")
		os.makedirs(cache_dir, exist_ok=True)
		return cache_dir

	def _load_auto(self):
		if self._load_from_cache_if_fresh():
			return

		try:
			self._update_cache_from_url()
			self._load_from_file()
		except Exception as e:
			print(f"Unable to update offsets from cs2-dumper: {e}")
			if not self._load_from_cache_if_exists():
				raise RuntimeError("No valid cached offsets found")

	def _load_from_cache_if_fresh(self):
		if not self._is_cache_fresh():
			return False
		return self._load_from_cache_if_exists()

	def _load_from_cache_if_exists(self):
		try:
			self._load_from_file()
			return True
		except Exception:
			return False

	def _is_cache_fresh(self):
		meta = self._read_meta()
		updated_at = meta.get("updated_at", 0)
		return isinstance(updated_at, (int, float)) and (time.time() - updated_at) < CACHE_MAX_AGE_SECONDS

	def _read_meta(self):
		if not os.path.exists(self._meta_file):
			return {}
		try:
			with open(self._meta_file, "r", encoding="utf-8") as f:
				return json.load(f)
		except Exception:
			return {}

	def _write_meta(self, meta):
		self._atomic_write_json(self._meta_file, meta)

	def _update_cache_from_url(self):
		meta = self._read_meta()
		etags = meta.get("etags", {}) if isinstance(meta.get("etags", {}), dict) else {}
		new_etags = dict(etags)

		for key, filename in CS2_DUMPER_FILES.items():
			url = f"{CS2_DUMPER_BASE_URL}/{filename}"
			cached_path = os.path.join(self._cache_dir, filename)
			etag = etags.get(filename)
			resp = self._request_json(url, etag=etag)

			if resp.status_code == 304:
				if not os.path.exists(cached_path):
					raise RuntimeError(f"Server returned 304 but cached file is missing: {filename}")
				continue

			resp.raise_for_status()
			payload = resp.json()
			self._validate_payload(key, payload)
			self._atomic_write_json(cached_path, payload)

			response_etag = resp.headers.get("ETag")
			if response_etag:
				new_etags[filename] = response_etag

		meta["etags"] = new_etags
		meta["updated_at"] = time.time()
		self._write_meta(meta)

	def _request_json(self, url, etag=None):
		headers = {"Accept": "application/json"}
		if etag:
			headers["If-None-Match"] = etag
		return requests.get(url, headers=headers, timeout=8)

	def _validate_payload(self, key, payload):
		if not isinstance(payload, dict):
			raise ValueError(f"Invalid payload for {key}: expected object")
		if "client.dll" not in payload:
			raise ValueError(f"Invalid payload for {key}: missing client.dll")

	def _atomic_write_json(self, path, data):
		dirname = os.path.dirname(path)
		os.makedirs(dirname, exist_ok=True)
		fd, temp_path = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=dirname)
		try:
			with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
				json.dump(data, tmp_file, indent=2)
			os.replace(temp_path, path)
		except Exception:
			if os.path.exists(temp_path):
				os.unlink(temp_path)
			raise

	def _load_from_file(self):
		base_path = self._cache_dir
		self.offsets = self._load_json_from_file(base_path, 'offsets.json')
		self.clientdll = self._load_json_from_file(base_path, 'client_dll.json')
		self.buttons = self._load_json_from_file(base_path, 'buttons.json')

	def _load_json_from_file(self, base_path, filename):
		with open(os.path.join(base_path, filename), 'r', encoding='utf-8') as f:
			return json.load(f)

	def offset(self, a):
		return self._get_value_from_dict(self.offsets, ['client.dll', a], f'Offset {a} not found.')

	def get(self, a, b):
		try:
			return self.clientdll["client.dll"]['classes'][a]['fields'][b]
		except KeyError as e:
			print(f"Warning: offset for {a} -> {b} not found: {e}")
			return 0

	def get_first(self, pairs):
		for a, b in pairs:
			value = self.get(a, b)
			if value:
				return value
		return 0

	def button(self, a):
		return self._get_value_from_dict(self.buttons, ['client.dll', a], f'Button {a} not found.')

	def _get_value_from_dict(self, data, keys, error_message):
		try:
			for key in keys:
				data = data[key]
			return data
		except KeyError:
			print(f"Warning: {error_message}")
			return 0


def get_offsets() -> Offset:
	global _OFFSETS_CACHE
	if _OFFSETS_CACHE is not None:
		return _OFFSETS_CACHE

	oc = Client()
	offsets_obj = Offset(
		dwViewMatrix=oc.offset("dwViewMatrix"),
		dwLocalPlayerPawn=oc.offset("dwLocalPlayerPawn"),
		dwEntityList=oc.offset("dwEntityList"),
		dwLocalPlayerController=oc.offset("dwLocalPlayerController"),
		dwViewAngles = oc.offset("dwViewAngles"),
		dwGameRules = oc.offset("dwGameRules"),
		dwSensitivity_sensitivity = oc.offset("dwSensitivity_sensitivity"),
		dwSensitivity = oc.offset("dwSensitivity"),
		

		ButtonJump=oc.button("jump"),
		
		m_hPlayerPawn=oc.get("CCSPlayerController", "m_hPlayerPawn"),
		m_iHealth=oc.get("C_BaseEntity", "m_iHealth"),
		m_lifeState=oc.get("C_BaseEntity", "m_lifeState"),
		m_iTeamNum=oc.get("C_BaseEntity", "m_iTeamNum"),
		m_vOldOrigin=oc.get("C_BasePlayerPawn", "m_vOldOrigin"),
		m_pGameSceneNode=oc.get("C_BaseEntity", "m_pGameSceneNode"),
		m_modelState=oc.get("CSkeletonInstance", "m_modelState"),
		m_boneArray=128,
		m_nodeToWorld=oc.get("CGameSceneNode", "m_nodeToWorld"),
		m_sSanitizedPlayerName=oc.get("CCSPlayerController", "m_sSanitizedPlayerName"),
		m_iIDEntIndex=oc.get("C_CSPlayerPawn", "m_iIDEntIndex"),
		m_flFlashMaxAlpha=oc.get("C_CSPlayerPawnBase", "m_flFlashMaxAlpha"),
		m_fFlags=oc.get("C_BaseEntity", "m_fFlags"),
		m_iFOV=oc.get("CCSPlayerBase_CameraServices", "m_iFOV"),
		m_pCameraServices=oc.get("C_BasePlayerPawn", "m_pCameraServices"),
		m_bIsScoped=oc.get("C_CSPlayerPawn", "m_bIsScoped"),
		m_vecViewOffset = oc.get_first([
			("C_BaseModelEntity", "m_vecViewOffset"),
			("C_BasePlayerPawn", "m_vecViewOffset"),
		]),
		m_entitySpottedState = oc.get("C_CSPlayerPawn", "m_entitySpottedState"),
		m_bSpotted = oc.get("EntitySpottedState_t", "m_bSpotted"),
		m_bBombPlanted = oc.get("C_CSGameRules", "m_bBombPlanted"),
		m_iShotsFired = oc.get("C_CSPlayerPawn", "m_iShotsFired"),
		m_aimPunchAngle = oc.get("C_CSPlayerPawn", "m_aimPunchAngle"),
		
		m_bSpottedByMask = oc.get("EntitySpottedState_t", "m_bSpottedByMask"),
		m_vecVelocity = oc.get("C_BaseEntity", "m_vecVelocity"),

		m_hPawn = oc.get_first([
			("CBasePlayerController", "m_hPawn"),
			("CCSPlayerController", "m_hPawn"),
		]),
		m_pObserverServices = oc.get("C_BasePlayerPawn", "m_pObserverServices"),
		m_hObserverTarget = oc.get("CPlayer_ObserverServices", "m_hObserverTarget"),
		m_iszPlayerName = oc.get_first([
			("CBasePlayerController", "m_iszPlayerName"),
			("CCSPlayerController", "m_iszPlayerName"),
		]),
		m_iObserverMode = oc.get("CPlayer_ObserverServices", "m_iObserverMode"),
	)
	_OFFSETS_CACHE = offsets_obj
	return offsets_obj

