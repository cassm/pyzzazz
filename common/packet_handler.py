from bitarray import bitarray
import struct


# FIXME probably make this less fragile. strict mode?
class StatePacketHeader:
    signature = 0xBEEE

    ops_by_byte = {0x00: "state_request",
                   0x01: "state_reply"}

    ops_by_str = {"state_request": 0x00,
                  "state_reply": 0x01}

    header_len = 5

    def __init__(self, opcode=-1, payload_len=-1):
        self.signature = self.signature
        self.opcode = opcode
        self.payload_len = payload_len

    def set_bytes(self, raw_bytes):
        assert len(raw_bytes) == self.header_len, \
            "selfHeader: invalid header length {}".format(len(raw_bytes))

        self.signature = raw_bytes[0] << 8 | raw_bytes[1]
        assert self.signature == self.signature, \
            "selfHeader: invalid signature {:04X}".format(self.signature)

        self.opcode = raw_bytes[2]
        assert self.opcode in self.ops_by_byte.keys(), \
            "selfHeader: invalid opcode {:02X}".format(self.opcode)

        self.payload_len = raw_bytes[3] << 8 | raw_bytes[4]

    def get_bytes(self):
        assert min(self.signature, self.opcode, self.payload_len) > 0, \
            "selfHeader: get_bytes called with uninitialised fields"

        header_bytes = bytearray()
        header_bytes.append(self.signature >> 8)
        header_bytes.append(self.signature & 0xff)
        header_bytes.append(self.opcode)
        header_bytes.append(self.payload_len >> 8)
        header_bytes.append(self.payload_len & 0xff)

        return header_bytes

class StateResponsePayload:
    def __init__(self, button_state=list(), slider_state=list()):
        self.button_state = button_state
        self.slider_state = slider_state

    def set_bytes(self, raw_bytes):
        assert len(raw_bytes <= 2), \
            "remaining length of packet is less than button bitfield width field"

        button_bitfield_width = raw_bytes[0] << 8 & raw_bytes[1]

        del(raw_bytes[0:2])

        assert len(raw_bytes <= button_bitfield_width), \
            "remaining length of packet is less than specified button bitfield width"

        for chunk in raw_bytes[0:button_bitfield_width]:
            for bit in range(8):
                self.button_state.append((chunk >> bit) & 1)

        del(raw_bytes[0:button_bitfield_width])

        assert len(raw_bytes <= 2), \
            "remaining length of packet is less than num sliders field"

        num_sliders = raw_bytes[0] << 8 & raw_bytes[1]

        assert len(raw_bytes <= num_sliders*2), \
            "remaining length of packet is less than specified button bitfield width"

        del(raw_bytes[0:2])

        for _ in range(num_sliders):
            self.slider_state.append(raw_bytes[0] << 8 & raw_bytes[1])
            del(raw_bytes[0:2])

    def get_bytes(self):
        state_bytes = bytearray()

        button_bitfield = bitarray(endian='little')

        for state in self.button_state:
            button_bitfield.append(state)

        # fill out to whole bytes
        # while len(button_bitfield) % 8 != 0:
        #     button_bitfield.append(False)

        # button bitfield width
        state_bytes.append(len(button_bitfield.tobytes()))

        # button bitfield
        state_bytes.extend(button_bitfield.tobytes())

        # number of slider vals
        state_bytes.append(len(self.slider_state))

        # slider vals
        for slider_val in self.slider_state:
            state_bytes.append(slider_val >> 8)
            state_bytes.append(slider_val & 0xff)

        return state_bytes


class StatePacketHandler:
    def __init__(self):
        self.available_packets = []
        self.buffer = list()
        self.header = StatePacketHeader()

    def add_bytes(self, new_bytes):
        for new_byte in new_bytes:
            self.buffer.append(new_byte)

            if len(self.buffer) == StatePacketHeader.header_len:
                self.header.set_bytes(self.buffer)

                # delete as we go for easier indexing
                del(self.buffer[0:StatePacketHeader.header_len])

            if self.header is not None and len(self.buffer) == self.header.payload_len:
                if StatePacketHeader.ops_by_byte[self.header.opcode] == "state_reply":
                    payload = StateResponsePayload()
                    payload.set_bytes(self.buffer)

                    self.available_packets.append("state_reply", payload)

                else:
                    raise Exception("StatePacketHandler: unhandled opcode {}".format(self.header.opcode))

                self.header = StatePacketHeader

    def clear(self):
        self.buffer = list()
        self.header = StatePacketHeader
