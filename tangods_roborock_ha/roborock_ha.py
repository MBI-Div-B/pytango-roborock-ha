from tango import AttrWriteType, DispLevel, DevState
from tango.server import Device, attribute, command, device_property, GreenMode
from importlib.resources import files
import numpy as np
import asyncio
from .rest_api_client import RestAPICachingClient


class RoborockHA(Device):
    green_mode = GreenMode.Asyncio

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

    vacuum_state = attribute(
        label="status",
        dtype=str,
    )

    def read_vacuum_state(self):
        return self._rest_api_client.get_state("vacuum.roborock_s7_pro_ultra").get("state")

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
        self.set_state(DevState.ON)

    def delete_device(self):
        Device.delete_device(self)
        self._rest_api_client.stop_fetch()
