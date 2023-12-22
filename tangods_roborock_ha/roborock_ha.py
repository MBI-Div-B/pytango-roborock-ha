from tango import AttrWriteType, DispLevel, DevState
from tango.server import Device, attribute, command, device_property, GreenMode
from importlib.resources import files
import numpy as np
from enum import IntEnum
import time
from .rest_api_client import RestAPICachingClient


class ROOM_IDS(IntEnum):
    ROOM1 = 0
    ROOM2 = 1
    ROOM3 = 2


class RoborockHA(Device):
    green_mode = GreenMode.Asyncio

    # entities in home assistant
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
    _ha_entities_type_access = {
        "sensor.roborock_s7_pro_ultra_last_clean_start": [str, AttrWriteType.READ],
        # "number.roborock_s7_pro_ultra_sound_volume": [int, AttrWriteType.READ_WRITE],
        "sensor.roborock_s7_pro_ultra_cleaning_progress": [float, AttrWriteType.READ],
        "sensor.roborock_s7_pro_ultra_current_clean_area": [float, AttrWriteType.READ],
        "sensor.roborock_s7_pro_ultra_current_clean_duration": [
            int,
            AttrWriteType.READ,
        ],
        "sensor.roborock_s7_pro_ultra_current_error": [int, AttrWriteType.READ],
        # "sensor.roborock_s7_pro_ultra_current_room": [str, AttrWriteType.READ],
        "sensor.roborock_s7_pro_ultra_dock_status": [str, AttrWriteType.READ],
        "sensor.roborock_s7_pro_ultra_last_clean_start": [str, AttrWriteType.READ],
        "sensor.roborock_s7_pro_ultra_last_clean_end": [str, AttrWriteType.READ],
        "sensor.roborock_s7_pro_ultra_total_clean_area": [float, AttrWriteType.READ],
        "sensor.roborock_s7_pro_ultra_total_clean_count": [int, AttrWriteType.READ],
        "sensor.roborock_s7_pro_ultra_total_duration": [int, AttrWriteType.READ],
        "sensor.roborock_s7_pro_ultra_total_dust_collection_count": [
            int,
            AttrWriteType.READ,
        ],
    }
    # attributes of vacuum robot itself
    _vacuum_query_attrs_types = {
        #'fan_speed_list': list,
        #'mop_mode_list': list,
        #'mop_intensity_list': list,
        "battery_level": int,
        #'battery_icon': str,
        "fan_speed": str,
        #'msgVer': int,
        #'msgSeq': int,
        "state": str,
        #'battery': int,
        "cleanTime": int,
        "cleanArea": int,
        "squareMeterCleanArea": float,
        "errorCode": int,
        #'mapPresent': int,
        "inCleaning": int,
        "inReturning": int,
        "inFreshState": int,
        #  'labStatus': int,
        #  'waterBoxStatus': int,
        #  'backType': int,
        #  'washPhase': int,
        #  'washReady': int,
        #  'fanPower': int,
        #  'dndEnabled': int,
        #  'mapStatus': int,
        #  'isLocating': int,
        #  'lockStatus': int,
        #  'waterBoxMode': int,
        #  'waterBoxCarriageStatus': int,
        #  'mopForbiddenEnable': int,
        #  'adbumperStatus': list,
        #  'waterShortageStatus': int,
        #  'dockType': int,
        "dustCollectionStatus": int,
        "autoDustCollection": int,
        #  'mopMode': int,
        #  'debugMode': int,
        #  'switchMapMode': int,
        #  'dockErrorStatus': int,
        #  'chargeStatus': int,
        #  'unsaveMapReason': int,
        #  'unsaveMapFlag': int,
        "status": str,
        "mop_mode": str,
        "mop_intensity": str,
        # "error": NoneType,
        #'icon': str,
        "friendly_name": str,
        #'supported_features': int
    }

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

    def dev_state(self):
        status_str, state_str = self._rest_api_client.get_state(
            "vacuum.roborock_s7_pro_ultra"
        ).get("attributes").get("status"), self._rest_api_client.get_state(
            "vacuum.roborock_s7_pro_ultra"
        ).get(
            "attributes"
        ).get(
            "state"
        )
        """
        roborock state can be:
        cleaning,
        returning,
        docked, idle
        status can be:
        charging,
        cleaning,
        error (if error then field "error" is not null"),
        washing_the_mop,
        charger_disconnected
        """

    def dev_status(self):
        template = "Status:\n{}\nState:\n{}"
        return template.format(
            self._rest_api_client.get_state("vacuum.roborock_s7_pro_ultra")
            .get("attributes")
            .get("status"),
            self._rest_api_client.get_state("vacuum.roborock_s7_pro_ultra")
            .get("attributes")
            .get("state"),
        )

    def always_executed_hook(self):
        now = time.time()
        if (now - self._last_query) > 1:
            self._rest_api_client.fetch_states()
            self._last_query = now

    def initialize_dynamic_attributes_from_vacuum_query(self):
        for attr_name, attr_type in self._vacuum_query_attrs_types.items():
            if attr_name == "state" or attr_name == "status":
                continue
            attr = attribute(
                name=attr_name,
                label=attr_name,
                dtype=attr_type,
                fget=self.read_vacuum_attr,
            )
            self.add_attribute(attr)

    def read_vacuum_attr(self, attr):
        attr_name = attr.get_name()
        return (
            self._rest_api_client.get_state("vacuum.roborock_s7_pro_ultra")
            .get("attributes")
            .get(attr_name)
        )

    def initialize_dynamic_attributes_from_ha_states(self):
        for attr_name, attr_list in self._ha_entities_type_access.items():
            attr = attribute(
                name=attr_name,
                label=attr_name.split(".")[-1],
                dtype=attr_list[0],
                access=attr_list[1],
                fget=self.read_ha_state,
            )
            self.add_attribute(attr)

    def read_ha_state(self, attr):
        attr_name = attr.get_name()
        dtype = self._ha_entities_type_access.get(attr_name)[0]
        return dtype(self._rest_api_client.get_state(attr_name).get("state"))

    clean_repeat = attribute(
        label="room clean repeat",
        dtype=int,
        access=AttrWriteType.READ_WRITE,
        memorized=True,
        hw_memorized=True,
    )

    def read_clean_repeat(self):
        return self._clean_repeat

    def write_clean_repeat(self, value):
        self._clean_repeat = value

    @command
    def start_cleaning_all(self):
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
    def start_clean_rooms(self, room_names):
        room_names = list(filter(lambda x: x != "", room_names))
        if all(room_name in self.ROBOROCK_ROOM_NAMES for room_name in room_names):
            print(room_names)
            room_ids = list(map(lambda x: self._rooms_dict.get(x), room_names))
            print(room_ids)
            self._rest_api_client.post_service(
                "vacuum",
                "send_command",
                {
                    "command": "app_segment_clean",
                    "entity_id": self.HA_ENTITY_ID,
                    "params": [{"segments": room_ids}, {"repeat": self._clean_repeat}],
                },
            )

    def init_device(self):
        Device.init_device(self)
        self.set_state(DevState.INIT)
        self._clean_repeat = 1
        self.get_device_properties()
        self._rest_api_client = RestAPICachingClient(
            self.HA_REST_API_URL,
            self.HA_TOKEN,
            self._ha_entities,
        )
        self.initialize_dynamic_attributes_from_vacuum_query()
        self.initialize_dynamic_attributes_from_ha_states()
        self._rooms_dict = dict(zip(self.ROBOROCK_ROOM_NAMES, self.ROBOROCK_ROOM_IDS))
        self._last_query = 0
        self.set_state(DevState.ON)

    def delete_device(self):
        Device.delete_device(self)
