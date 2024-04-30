import re

# Class copied from portconfig odule in sonic
PORT_STR = "Ethernet"
BRKOUT_PATTERN = r'(\d{1,6})x(\d{1,6}G?)(\[(\d{1,6}G?,?)*\])?(\((\d{1,6})\))?'
BRKOUT_PATTERN_GROUPS = 6

class BreakoutCfg(object):

    class BreakoutModeEntry:
        def __init__(self, num_ports, default_speed, supported_speed, num_assigned_lanes=None):
            self.num_ports = int(num_ports)
            self.default_speed = self._speed_to_int(default_speed)
            self.supported_speed = set((self.default_speed, ))
            self._parse_supported_speed(supported_speed)
            self.num_assigned_lanes = self._parse_num_assigned_lanes(num_assigned_lanes)

        @classmethod
        def _speed_to_int(cls, speed):
            try:
                if speed.endswith('G'):
                    return int(speed.replace('G', '')) * 1000
                elif speed.endswith('M'):
                    return int(speed.replace('M', '')) * 100

                return int(speed)
            except ValueError:
                raise RuntimeError("Unsupported speed format '{}'".format(speed))

        def _parse_supported_speed(self, speed):
            if not speed:
                return

            if not speed.startswith('[') and not speed.endswith(']'):
                raise RuntimeError("Unsupported port breakout format!")

            for s in speed[1:-1].split(','):
                self.supported_speed.add(self._speed_to_int(s.strip()))

        def _parse_num_assigned_lanes(self, num_assigned_lanes):
            if not num_assigned_lanes:
                return

            if isinstance(num_assigned_lanes, int):
                return num_assigned_lanes

            if not num_assigned_lanes.startswith('(') and not num_assigned_lanes.endswith(')'):
                raise RuntimeError("Unsupported port breakout format!")

            return int(num_assigned_lanes[1:-1])

        def __eq__(self, other):
            if isinstance(other, BreakoutCfg.BreakoutModeEntry):
                if self.num_ports != other.num_ports:
                    return False
                if self.supported_speed != other.supported_speed:
                    return False
                if self.num_assigned_lanes != other.num_assigned_lanes:
                    return False
                return True
            else:
                return False

        def __ne__(self, other):
            return not self == other

        def __hash__(self):
            return hash((self.num_ports, tuple(self.supported_speed), self.num_assigned_lanes))

    def __init__(self, name, bmode, properties):
        self._interface_base_id = int(name.replace(PORT_STR, ''))
        self._properties = properties
        self._lanes = properties ['lanes'].split(',')
        self._indexes = properties ['index'].split(',')
        try:
            self._intf_ids = properties ['interface_ids'].split(',')
        except:
            self._intf_ids = ""
        self._breakout_mode_entry = self._str_to_entries(bmode)
        self._breakout_capabilities = None

        # Find specified breakout mode in port breakout mode capabilities
        for supported_mode in self._properties['breakout_modes']:
            if self._breakout_mode_entry == self._str_to_entries(supported_mode):
                self._breakout_capabilities = self._properties['breakout_modes'][supported_mode]
                break

        if not self._breakout_capabilities:
            raise RuntimeError("Unsupported breakout mode {}!".format(bmode))

    def _re_group_to_entry(self, group):
        if len(group) != BRKOUT_PATTERN_GROUPS:
            raise RuntimeError("Unsupported breakout mode format!")

        num_ports, default_speed, supported_speed, _, num_assigned_lanes, _ = group
        if not num_assigned_lanes:
            num_assigned_lanes = len(self._lanes)

        return BreakoutCfg.BreakoutModeEntry(num_ports, default_speed, supported_speed, num_assigned_lanes)

    def _str_to_entries(self, bmode):
        """
        Example of match_list for some breakout_mode using regex
            Breakout Mode -------> Match_list
            -----------------------------
            2x25G(2)+1x50G(2) ---> [('2', '25G', None, '(2)', '2'), ('1', '50G', None, '(2)', '2')]
            1x50G(2)+2x25G(2) ---> [('1', '50G', None, '(2)', '2'), ('2', '25G', None, '(2)', '2')]
            1x100G[40G] ---------> [('1', '100G', '[40G]', None, None)]
            2x50G ---------------> [('2', '50G', None, None, None)]
        """

        try:
            groups_list = [re.match(BRKOUT_PATTERN, i).groups() for i in bmode.split("+")]
        except Exception as e:
            print(e)
            raise RuntimeError('Breakout mode "{}" validation failed!'.format(bmode))

        return [self._re_group_to_entry(group) for group in groups_list]

    def get_config(self):
        # Ensure that we have corret number of configured lanes
        lanes_used = 0
        for entry in self._breakout_mode_entry:
            lanes_used += entry.num_assigned_lanes

        if lanes_used > len(self._lanes):
            raise RuntimeError("Assigned lanes count is more that available!")

        ports = {}

        lane_id = 0
        alias_id = 0

        for entry in self._breakout_mode_entry:
            lanes_per_port = entry.num_assigned_lanes // entry.num_ports

            for port in range(entry.num_ports):
                if self._intf_ids:
                    interface_name = PORT_STR + str(self._intf_ids[lane_id])
                else:
                    interface_name = PORT_STR + str(self._interface_base_id + lane_id)

                lanes = self._lanes[lane_id:lane_id + lanes_per_port]

                ports[interface_name] = {
                    'alias': self._breakout_capabilities[alias_id],
                    'lanes': ','.join(lanes),
                    'speed': str(entry.default_speed),
                    'index': self._indexes[lane_id],
                    'parent_port': PORT_STR + str(self._interface_base_id)
                }

                lane_id += lanes_per_port
                alias_id += 1

        return ports

    def get_supported_speed(self):
        # Ensure that we have corret number of configured lanes
        lanes_used = 0
        for entry in self._breakout_mode_entry:
            lanes_used += entry.num_assigned_lanes

        if lanes_used > len(self._lanes):
            raise RuntimeError("Assigned lanes count is more that available!")

        port_speed_dict = {}

        lane_id = 0
        alias_id = 0

        for entry in self._breakout_mode_entry:
            lanes_per_port = entry.num_assigned_lanes // entry.num_ports

            for port in range(entry.num_ports):
                if self._intf_ids:
                    interface_name = PORT_STR + str(self._intf_ids[lane_id])
                else:
                    interface_name = PORT_STR + str(self._interface_base_id + lane_id)

                lanes = self._lanes[lane_id:lane_id + lanes_per_port]

                port_speed_dict[interface_name] = entry.supported_speed

                lane_id += lanes_per_port
                alias_id += 1

        return port_speed_dict
