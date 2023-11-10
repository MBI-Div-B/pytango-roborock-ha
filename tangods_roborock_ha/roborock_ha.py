from tango import AttrWriteType, DispLevel, DevState
from tango.server import Device, attribute, command, device_property, GreenMode
from importlib.resources import files
import numpy as np
from enum import IntEnum
from .rest_api_client import RestAPICachingClient


class ROOM_IDS(IntEnum):
    ROOM1 = 0
    ROOM2 = 1
    ROOM3 = 2


class RoborockHA(Device):
    green_mode = GreenMode.Asyncio

    _ha_entities = (
        "vacuum.roborock_s7_pro_ultra",
        "sensor.roborock_s7_pro_ultra_last_clean_start",
        "number.roborock_s7_pro_ultra_sound_volume",
        "sensor.roborock_s7_pro_ultra_cleaning_progress",
        "sensor.roborock_s7_pro_ultra_current_clean_area",
        "sensor.roborock_s7_pro_ultra_current_clean_duration",
        "sensor.roborock_s7_pro_ultra_current_error",
        "sensor.roborock_s7_pro_ultra_current_room",
        "sensor.roborock_s7_pro_ultra_dock_status",
        "sensor.roborock_s7_pro_ultra_last_clean_start",
        "sensor.roborock_s7_pro_ultra_last_clean_end",
        "sensor.roborock_s7_pro_ultra_total_clean_area",
        "sensor.roborock_s7_pro_ultra_total_clean_count",
        "sensor.roborock_s7_pro_ultra_total_duration",
        "sensor.roborock_s7_pro_ultra_total_dust_collection_count",
    )

    """
    {
    "entity_id": "vacuum.roborock_s7_pro_ultra",
    "state": "docked",
    "attributes": {
        "fan_speed_list": [
            "off",
            "quiet",
            "balanced",
            "turbo",
            "max",
            "custom",
            "max_plus"
        ],
        "mop_mode_list": [
            "standard",
            "deep",
            "custom",
            "deep_plus"
        ],
        "mop_intensity_list": [
            "off",
            "mild",
            "moderate",
            "intense",
            "custom"
        ],
        "battery_level": 100,
        "battery_icon": "mdi:battery-charging-100",
        "fan_speed": "max",
        "msgVer": 2,
        "msgSeq": 168,
        "state": "docked",
        "battery": 100,
        "cleanTime": 13,
        "cleanArea": 0,
        "squareMeterCleanArea": 0.0,
        "errorCode": 0,
        "mapPresent": 1,
        "inCleaning": 0,
        "inReturning": 0,
        "inFreshState": 1,
        "labStatus": 1,
        "waterBoxStatus": 1,
        "backType": -1,
        "washPhase": 0,
        "washReady": 0,
        "fanPower": 104,
        "dndEnabled": 0,
        "mapStatus": 3,
        "isLocating": 0,
        "lockStatus": 0,
        "waterBoxMode": 201,
        "waterBoxCarriageStatus": 1,
        "mopForbiddenEnable": 1,
        "adbumperStatus": [
            0,
            0,
            0
        ],
        "waterShortageStatus": 0,
        "dockType": 3,
        "dustCollectionStatus": 0,
        "autoDustCollection": 1,
        "mopMode": 302,
        "debugMode": 0,
        "switchMapMode": 0,
        "dockErrorStatus": 0,
        "chargeStatus": 1,
        "unsaveMapReason": 4,
        "unsaveMapFlag": 0,
        "status": "charging",
        "mop_mode": "custom",
        "mop_intensity": "mild",
        "error": null,
        "icon": "mdi:robot-vacuum",
        "friendly_name": "Roborock S7 Pro Ultra",
        "supported_features": 16383
    },
    "last_changed": "2023-11-10T13:42:47.096104+00:00",
    "last_updated": "2023-11-10T16:24:16.156867+00:00",
    "context": {
        "id": "01HEX0RS0WJMD9X0V1FHM2KJPC",
        "parent_id": null,
        "user_id": null
    }
}
    """

    _vacuum_query_attributes = (
        "fan_speed_list",
        "mop_mode_list",
        "mop_intensity_list",
        "battery_level",
        "battery_icon",
        "fan_speed",
        "msgVer",
        "msgSeq",
        "state",
        "battery",
        "cleanTime",
        "cleanArea",
        "squareMeterCleanArea",
        "errorCode",
        "mapPresent",
        "inCleaning",
        "inReturning",
        "inFreshState",
        "labStatus",
        "waterBoxStatus",
        "backType",
        "washPhase",
        "washReady",
        "fanPower",
        "dndEnabled",
        "mapStatus",
        "isLocating",
        "lockStatus",
        "waterBoxMode",
        "waterBoxCarriageStatus",
        "mopForbiddenEnable",
        "adbumperStatus",
        "waterShortageStatus",
        "dockType",
        "dustCollectionStatus",
        "autoDustCollection",
        "mopMode",
        "debugMode",
        "switchMapMode",
        "dockErrorStatus",
        "chargeStatus",
        "unsaveMapReason",
        "unsaveMapFlag",
        "status",
        "mop_mode",
        "mop_intensity",
        "error",
        "icon",
        "friendly_name",
        "supported_features",
    )

    HA_REST_API_URL = device_property(
        str,
        doc="http://ampere.mbi-berlin.de:8123/api/",
        mandatory=True,
    )
    HA_TOKEN = device_property(
        str,
        doc="generated from user",
        mandatory=True,
    )
    REST_API_POLLING_PERIOD = device_property(
        int,
        doc="generated from user",
        default_value=10,
    )
    HA_ENTITY_ID = device_property(
        str,
        doc="see in services, choose as target, yaml mode\nSomething like: vacuum.roborock_s7_pro_ultra",
        mandatory=True,
    )
    ROBOROCK_ROOM_NAMES = device_property(
        (str,), doc="list of room names", mandatory=True
    )
    ROBOROCK_ROOM_IDS = device_property(
        (int,),
        doc="ids of rooms (see https://www.home-assistant.io/integrations/roborock/#how-can-i-clean-a-specific-room)",
        mandatory=True,
    )

    vacuum_state = attribute(
        label="state",
        dtype=str,
    )
    vacuum_status = attribute(
        label="status",
        dtype=str,
    )
    clean_repeat = attribute(
        label="clean repeat",
        dtype=int,
        access=AttrWriteType.READ_WRITE,
    )

    def read_clean_repeat(self):
        return self._clean_repeat

    def write_clean_repeat(self, value):
        self._clean_repeat = value

    def read_vacuum_state(self):
        return self._rest_api_client.get_state("vacuum.roborock_s7_pro_ultra").get(
            "state"
        )
    
    def read_vacuum_status(self):
        return self._rest_api_client.get_state("vacuum.roborock_s7_pro_ultra").get("attributes").get(
            "status"
        )

    @command
    def start_cleaning(self):
        self._rest_api_client.post_service(
            "vacuum", "start", {"entity_id": self.HA_ENTITY_ID}
        )

    @command
    def pause_cleaning(self):
        self._rest_api_client.post_service(
            "vacuum", "pause", {"entity_id": self.HA_ENTITY_ID}
        )
    @command
    def stop_cleaning(self):
        self._rest_api_client.post_service(
            "vacuum", "stop", {"entity_id": self.HA_ENTITY_ID}
        )

    @command
    def return_to_dock(self):
        self._rest_api_client.post_service(
            "vacuum", "return_to_base", {"entity_id": self.HA_ENTITY_ID}
        )

    @command(dtype_in=(str,))
    def clean_rooms(self, room_names):
        room_names = list(filter(lambda x: x != "", room_names))
        if all(room_name in self.ROBOROCK_ROOM_NAMES for room_name in room_names):
            print(room_names)
            room_ids = list(map(lambda x: self._rooms_dict.get(x), room_names))
            print(room_ids)
            self._rest_api_client.post_service(
                "vacuum",
                "send_command",
                {"command": "app_segment_clean",
                 "entity_id": self.HA_ENTITY_ID,
                 "params": [{"segments": room_ids}, {"repeat": 1}]},
            )

    def init_device(self):
        Device.init_device(self)
        self.set_state(DevState.INIT)
        self.get_device_properties()
        self._rest_api_client = RestAPICachingClient(
            self.HA_REST_API_URL,
            self.HA_TOKEN,
            self.REST_API_POLLING_PERIOD,
            (
                "vacuum.roborock_s7_pro_ultra",
                "sensor.roborock_s7_pro_ultra_last_clean_start",
            ),
        )
        self._rooms_dict = dict(zip(self.ROBOROCK_ROOM_NAMES, self.ROBOROCK_ROOM_IDS))
        self.set_state(DevState.ON)

    def delete_device(self):
        Device.delete_device(self)
        self._rest_api_client.stop_fetch()
