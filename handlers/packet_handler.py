from bitarray import bitarray


# FIXME probably make this less fragile. strict mode?
class CommHeader:
    signature = ord("~")

    ops_by_byte = {0x00: "name_request",
                   0x01: "name_reply",
                   0x02: "state_request",
                   0x03: "state_reply"}

    ops_by_str = {"name_request": 0x00,
                  "name_reply": 0x01,
                  "state_request": 0x02,
                  "state_reply": 0x03}

    header_len = 4

    def __init__(self, payload_len=0, msgtype=None, bytes=None):
        if bytes:
            assert msgtype is None, "Header must be instantiated with either a bytestream or a type"
            self.set_bytes(bytes)

        else:
            assert msgtype is not None, "Header must be instantiated with either a bytestream or a type"
            self.signature = self.signature
            self.payload_len = payload_len
            self.opcode = self.ops_by_str[msgtype]

    def set_bytes(self, raw_bytes):
        assert len(raw_bytes) == self.header_len, \
            "selfHeader: invalid header length {}".format(len(raw_bytes))

        self.signature = int(raw_bytes[0])
        assert self.signature == self.signature, \
            "selfHeader: invalid signature {:04X}".format(self.signature)

        self.opcode = raw_bytes[1]
        assert self.opcode in self.ops_by_byte.keys(), \
            "selfHeader: invalid opcode {:02X}".format(self.opcode)

        self.payload_len = raw_bytes[2] << 8 | raw_bytes[3]

    def get_bytes(self):
        assert min(self.signature, self.opcode, self.payload_len) >= 0, \
            "selfHeader: get_bytes called with uninitialised fields"

        header_bytes = bytearray()
        header_bytes.append(self.signature)
        header_bytes.append(self.opcode)
        header_bytes.append(self.payload_len >> 8)
        header_bytes.append(self.payload_len & 0xff)

        return header_bytes

    def get_dict(self):
        return {"msgtype": self.ops_by_byte[self.opcode],
                "payload_len": self.payload_len}


class NameReplyPayload:
    def __init__(self, name=None, bytes=None):
        if bytes is not None:
            assert name is None, "Payload must be initialised with either values or a bytestream"
            self.set_bytes(bytes)

        else:
            assert name is not None, "Payload must be initialised with either values or a bytestream"
            self.name = name

    def set_bytes(self, raw_bytes):
        self.name = raw_bytes.decode('ascii')

    def get_bytes(self):
        return bytes(map(ord, self.name))

    def get_dict(self):
        return {"msgtype": "name_reply",
                "name": self.name}


class StateReplyPayload:
    def __init__(self, button_state=None, slider_state=None, bytes=None):
        if bytes is not None:
            assert button_state is None and slider_state is None,\
                "Payload must be initialised with either values or a bytestream"
            self.slider_state = []
            self.button_state = []
            self.set_bytes(bytes)

        else:
            assert button_state is not None and slider_state is not None, \
                "Payload must be initialised with either values or a bytestream"
            self.button_state = button_state
            self.slider_state = slider_state

    def set_bytes(self, raw_bytes):
        assert len(raw_bytes) >= 1, \
            "remaining length of packet is less than button bitfield width field"

        button_bitfield_width = int(raw_bytes[0])

        del(raw_bytes[0])

        assert len(raw_bytes) >= button_bitfield_width, \
            "remaining length of packet {} is less than specified button bitfield width {}".format(len(raw_bytes), button_bitfield_width)

        for chunk in raw_bytes[0:button_bitfield_width]:
            for bit in range(8):
                self.button_state.append((chunk >> (7-bit)) & 1)

        del(raw_bytes[0:button_bitfield_width])

        assert len(raw_bytes) >= 1, \
            "remaining length of packet is less than num sliders field"

        num_sliders = int(raw_bytes[0])

        assert len(raw_bytes) >= num_sliders*2, \
            "remaining length of packet is less than specified button bitfield width"

        del(raw_bytes[0])

        for _ in range(num_sliders):
            self.slider_state.append(raw_bytes[0] << 8 | raw_bytes[1])
            del(raw_bytes[0:2])

    def get_bytes(self):
        state_bytes = bytearray()

        button_bitfield = bitarray(endian='big')

        for state in self.button_state:
            button_bitfield.append(state)

        # fill out to whole bytes
        # while len(button_bitfield) % 8 != 0:
        #     button_bitfield.append(False)

        # button bitfield width
        bitfield_width = len(button_bitfield.tobytes())
        state_bytes.extend(bitfield_width.to_bytes(1, signed=False))

        # button bitfield
        state_bytes.extend(button_bitfield.tobytes())

        # number of slider vals
        state_bytes.extend(len(self.slider_state).to_bytes(1, signed=False))

        # slider vals
        for slider_val in self.slider_state:
            state_bytes.append(slider_val >> 8)
            state_bytes.append(slider_val & 0xff)

        return state_bytes

    def get_dict(self):
        return {"msgtype": "state_reply",
                "slider_state": self.slider_state,
                "button_state": self.button_state}


class CommPacketHandler:
    def __init__(self):
        self.available_packets = []
        self.buffer = bytearray()
        self.header = None

    def add_bytes(self, new_bytes):
        for new_byte in new_bytes:
            self.buffer.append(new_byte)

            if self.header is None and len(self.buffer) == CommHeader.header_len:
                self.header = CommHeader(bytes=self.buffer)

                # delete as we go for easier indexing
                del(self.buffer[0:CommHeader.header_len])

            if self.header is not None and len(self.buffer) == self.header.payload_len:
                if CommHeader.ops_by_byte[self.header.opcode] == "name_request":
                    # print("received name request")
                    self.available_packets.append(self.header.get_dict())

                elif CommHeader.ops_by_byte[self.header.opcode] == "name_reply":
                    # print("received name reply")
                    payload = NameReplyPayload(bytes=self.buffer)
                    self.available_packets.append(payload.get_dict())

                elif CommHeader.ops_by_byte[self.header.opcode] == "state_request":
                    # print("received state request")
                    self.available_packets.append(self.header.get_dict())

                elif CommHeader.ops_by_byte[self.header.opcode] == "state_reply":
                    # print("received state reply")
                    payload = StateReplyPayload(bytes=self.buffer)
                    self.available_packets.append(payload.get_dict())

                else:
                    raise Exception("StatePacketHandler: unhandled opcode {}".format(self.header.opcode))

                del(self.buffer[0:self.header.payload_len])

                self.header = None

    def clear(self):
        self.buffer = bytearray()
        self.header = None
