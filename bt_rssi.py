import bluetooth
import bluetooth._bluetooth as bt
import struct
import array
import fcntl


class BluetoothRSSI(object):
    """Object class for getting the RSSI value of a Bluetooth address."""

    def __init__(self, addr):
        self.addr = addr
        self.hci_sock = bt.hci_open_dev()
        self.hci_fd = self.hci_sock.fileno()
        self.bt_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        self.bt_sock.settimeout(10)
        self.closed = False
        self.connected = False
        self.cmd_pkt = None

    def prep_cmd_pkt(self):
        """Prepare the command packet for requesting RSSI."""
        reqstr = struct.pack(
            b'6sB17s', bt.str2ba(self.addr), bt.ACL_LINK, b'\0' * 17)
        request = array.array('b', reqstr)
        handle = fcntl.ioctl(self.hci_fd, bt.HCIGETCONNINFO, request, 1)
        handle = struct.unpack(b'8xH14x', request.tostring())[0]
        self.cmd_pkt = struct.pack('H', handle)

    def connect(self):
        """Connect to the Bluetooth device."""
        # Connecting via PSM 1 - Service Discovery
        self.bt_sock.connect_ex((self.addr, 1))
        self.connected = True
    
    def close(self):
        """Close the bluetooth socket."""
        self.bt_sock.close()
        self.hci_sock.close()
        self.closed = True

    def request_rssi(self):
        """Request the current RSSI value.
        @return: The RSSI value or None if the device connection fails
                 (i.e. the device is not in range).
        """
        try:
            # If socket is closed, return nothing
            if self.closed:
                return None
            # Only do connection if not already connected
            if not self.connected:
                self.connect()
            # Command packet prepared each iteration to allow disconnect to trigger IOError
            self.prep_cmd_pkt()
            # Send command to request RSSI
            rssi = bt.hci_send_req(
                self.hci_sock, bt.OGF_STATUS_PARAM,
                bt.OCF_READ_RSSI, bt.EVT_CMD_COMPLETE, 4, self.cmd_pkt)
            rssi = struct.unpack('b', rssi[3].to_bytes(1, 'big'))
            return rssi
        except IOError:
            # Happens if connection fails (e.g. device is not in range)
            self.connected = False
            # Socket recreated to allow device to successfully reconnect
            self.bt_sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
            return None