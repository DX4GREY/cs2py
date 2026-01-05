import pyMeow as pw
from ext.offsets import get_offsets

class SpectatorList:
    def __init__(self):
        self.process = pw.open_process("cs2.exe")
        self.client = pw.get_module(self.process, "client.dll")["base"]

        off = get_offsets()
        self.dwEntityList = off.dwEntityList
        self.dwLocalPlayerController = off.dwLocalPlayerController

        self.m_hPawn = off.m_hPawn
        self.m_iszPlayerName = off.m_iszPlayerName
        self.m_pObserverServices = off.m_pObserverServices
        self.m_hObserverTarget = off.m_hObserverTarget
        self.m_iObserverMode = off.m_iObserverMode
        self.m_iTeamNum = off.m_iTeamNum

        self.max_players = 64
        self.debug = False

    def debug_log(self, msg):
        if self.debug:
            print(msg)

    def get_entity(self, handle):
        if handle <= 0:
            return 0
        entity_list = pw.r_int64(self.process, self.client + self.dwEntityList)
        list_entry = pw.r_int64(self.process, entity_list + (0x8 * ((handle & 0x7FFF) >> 9)) + 0x10)
        return pw.r_int64(self.process, list_entry + 0x70 * (handle & 0x7FF))

    def get_spectators(self):
        specs = []

        # ================= LOCAL CONTROLLER =================
        local_controller = pw.r_int64(self.process, self.client + self.dwLocalPlayerController)
        if not local_controller:
            return specs

        local_pawn_handle = pw.r_int(self.process, local_controller + self.m_hPawn)
        local_pawn = self.get_entity(local_pawn_handle)

        local_team = pw.r_int(self.process, local_pawn + self.m_iTeamNum) if local_pawn else 0
        local_target_pawn = local_pawn

        # ================= HANDLE LOCAL DEAD =================
        if local_pawn:
            obs_services = pw.r_int64(self.process, local_pawn + self.m_pObserverServices)
            if obs_services:
                target_handle = pw.r_int(self.process, obs_services + self.m_hObserverTarget)
                if target_handle > 0:
                    local_target_pawn = self.get_entity(target_handle)

        if not local_target_pawn:
            return specs

        # ================= LOOP PLAYER =================
        for i in range(1, self.max_players):
            try:
                controller = self.get_entity(i)
                if not controller or controller == local_controller:
                    continue

                pawn_handle = pw.r_int(self.process, controller + self.m_hPawn)
                pawn = self.get_entity(pawn_handle)
                if not pawn:
                    continue

                obs_services = pw.r_int64(self.process, pawn + self.m_pObserverServices)
                if not obs_services:
                    continue

                target_handle = pw.r_int(self.process, obs_services + self.m_hObserverTarget)
                target_pawn = self.get_entity(target_handle)

                if target_pawn != local_target_pawn:
                    continue

                # ================= INFO =================
                name = pw.r_string(self.process, controller + self.m_iszPlayerName, 64).split("\x00")[0]
                team = pw.r_int(self.process, pawn + self.m_iTeamNum)
                obs_mode = pw.r_int(self.process, obs_services + self.m_iObserverMode)

                self.debug_log(f"[DEBUG] Player {i}: Name={name}, Team={team}, ObsMode={obs_mode}")
                specs.append(name)

            except Exception as e:
                self.debug_log(f"[EXCEPTION] Player {i}: {e}")

        return specs
