# Usage: python3 test_expt.py /path/to/src /path/to/dst /path/to/dev
# Parameters:
#  /path/to/src: path to input file
#  /path/to/dst: destination directory for output file
#  /path/to/dev: path to device, e.g. /dev/ttyUSB0
# Output:
#  out.hex: The hex-format replies to the input commands

# import Python modules
import copy     # deepcopy
import datetime # datetime
import enum     # Enum
import math     # floor
import serial   # serial
import sys      # accessing script arguments
import time     # sleep

################################################################################

# Special values for testing the EXPT board

HWID  = 0x5441
msgid = 0x0000
SRC   = 0x00
DST   = 0x02

# "constants"

## TAOLST General Constants
CMD_MAX_LEN  = 258
DATA_MAX_LEN = 249
START_BYTE_0 = 0x22
START_BYTE_1 = 0x69
DEST_COMM    = 0x01
DEST_CTRL    = 0x0a
DEST_EXPT    = 0x02
DEST_TERM    = 0x00

## TAOLST Command Op Codes
APP_GET_TELEM_OPCODE         = 0x17
APP_GET_TIME_OPCODE          = 0x13
APP_REBOOT_OPCODE            = 0x12
APP_SET_TIME_OPCODE          = 0x14
APP_TELEM_OPCODE             = 0x18
BOOTLOADER_ACK_OPCODE        = 0x01
BOOTLOADER_ERASE_OPCODE      = 0x0c
BOOTLOADER_JUMP_OPCODE       = 0x0b
BOOTLOADER_NACK_OPCODE       = 0x0f
BOOTLOADER_PING_OPCODE       = 0x00
BOOTLOADER_WRITE_PAGE_OPCODE = 0x02
COMMON_ACK_OPCODE            = 0x10
COMMON_ASCII_OPCODE          = 0x11
COMMON_DATA_OPCODE           = 0x16
COMMON_NACK_OPCODE           = 0xff

## TAOLST Command Enum Parameters
BOOTLOADER_ACK_REASON_PONG   = 0x00
BOOTLOADER_ACK_REASON_ERASED = 0x01
BOOTLOADER_ACK_REASON_JUMP   = 0xff

## TAOLST Command Indices
START_BYTE_0_INDEX = 0
START_BYTE_1_INDEX = 1
MSG_LEN_INDEX      = 2
HWID_LSB_INDEX     = 3
HWID_MSB_INDEX     = 4
MSG_ID_LSB_INDEX   = 5
MSG_ID_MSB_INDEX   = 6
DEST_ID_INDEX      = 7
OPCODE_INDEX       = 8
DATA_START_INDEX   = 9

## Space time epoch
J2000 = datetime.datetime(\
 2000, 1, 1,11,58,55,816000,\
 tzinfo=datetime.timezone.utc\
)

# enums

class RxCmdBuffState(enum.Enum):
  START_BYTE_0 = 0x00
  START_BYTE_1 = 0x01
  MSG_LEN      = 0x02
  HWID_LSB     = 0x03
  HWID_MSB     = 0x04
  MSG_ID_LSB   = 0x05
  MSG_ID_MSB   = 0x06
  DEST_ID      = 0x07
  OPCODE       = 0x08
  DATA         = 0x09
  COMPLETE     = 0x0a

# helper functions

## Converts DEST_ID to string
def dest_id_to_str(dest_id):
  if dest_id==DEST_COMM:
    return 'comm'
  elif dest_id==DEST_CTRL:
    return 'ctrl'
  elif dest_id==DEST_EXPT:
    return 'expt'
  elif dest_id==DEST_TERM:
    return 'term'
  else:
    return '?'

## Converts BOOTLOADER_ACK_REASON to string
def bootloader_ack_reason_to_str(bootloader_ack_reason):
  if bootloader_ack_reason==BOOTLOADER_ACK_REASON_PONG:
    return 'pong'
  elif bootloader_ack_reason==BOOTLOADER_ACK_REASON_ERASED:
    return 'erased'
  elif bootloader_ack_reason==BOOTLOADER_ACK_REASON_JUMP:
    return 'jump'
  else:
    return '?'

## Converts a list of command bytes (ints) to a human-readable string
def cmd_bytes_to_str(data):
  s = ''
  extra = ''
  if data[OPCODE_INDEX] == APP_GET_TELEM_OPCODE:
    s += 'app_get_telem'
  elif data[OPCODE_INDEX] == APP_GET_TIME_OPCODE:
    s += 'app_get_time'
  elif data[OPCODE_INDEX] == APP_REBOOT_OPCODE:
    s += 'app_reboot'
    if data[MSG_LEN_INDEX] == 0x0a:
      extra = ' delay:'+str(\
       (data[DATA_START_INDEX+3]<<24) | \
       (data[DATA_START_INDEX+2]<<16) | \
       (data[DATA_START_INDEX+1]<< 8) | \
       (data[DATA_START_INDEX+0]<< 0)   \
      )
  elif data[OPCODE_INDEX] == APP_SET_TIME_OPCODE:
    s += 'app_set_time'
    extra = \
     ' sec:' + str(\
      data[DATA_START_INDEX+3]<<24 | \
      data[DATA_START_INDEX+2]<<16 | \
      data[DATA_START_INDEX+1]<< 8 | \
      data[DATA_START_INDEX+0]<< 0   \
     ) + \
     ' ns:'  + str(\
      data[DATA_START_INDEX+7]<<24 | \
      data[DATA_START_INDEX+6]<<16 | \
      data[DATA_START_INDEX+5]<< 8 | \
      data[DATA_START_INDEX+4]<< 0   \
     )
  elif data[OPCODE_INDEX] == APP_TELEM_OPCODE:
    s += 'app_telem'
    extra = ' hex_telem:'
    for i in range(0,data[MSG_LEN_INDEX]-0x06):
      extra += '{:02x}'.format(data[DATA_START_INDEX+i])
  elif data[OPCODE_INDEX] == BOOTLOADER_ACK_OPCODE:
    s += 'bootloader_ack'
    if data[MSG_LEN_INDEX] == 0x07:
      extra = ' reason:'+'0x{:02x}'.format(data[DATA_START_INDEX])+\
       '('+bootloader_ack_reason_to_str(data[DATA_START_INDEX])+')'
  elif data[OPCODE_INDEX] == BOOTLOADER_ERASE_OPCODE:
    s += 'bootloader_erase'
    if data[MSG_LEN_INDEX] == 0x07:
      extra = ' status:'+'0x{:02x}'.format(data[DATA_START_INDEX])
  elif data[OPCODE_INDEX] == BOOTLOADER_JUMP_OPCODE:
    s += 'bootloader_jump'
  elif data[OPCODE_INDEX] == BOOTLOADER_NACK_OPCODE:
    s += 'bootloader_nack'
  elif data[OPCODE_INDEX] == BOOTLOADER_PING_OPCODE:
    s += 'bootloader_ping'
  elif data[OPCODE_INDEX] == BOOTLOADER_WRITE_PAGE_OPCODE:
    s += 'bootloader_write_page'
    extra = ' subpage_id:'+str(data[DATA_START_INDEX])
    if data[MSG_LEN_INDEX] == 0x87:
      extra += ' hex_data:'
      for i in range(0,data[MSG_LEN_INDEX]-0x07):
        extra += '{:02x}'.format(data[DATA_START_INDEX+1+i])
  elif data[OPCODE_INDEX] == COMMON_ACK_OPCODE:
    s += 'common_ack'
  elif data[OPCODE_INDEX] == COMMON_ASCII_OPCODE:
    s += 'common_ascii'
    extra = ' "'
    for i in range(0,data[MSG_LEN_INDEX]-0x06):
      extra += chr(data[DATA_START_INDEX+i])
    extra += '"'
  elif data[OPCODE_INDEX] == COMMON_DATA_OPCODE:
      s += 'common_data'
      extra += ' hex_payload: '
      for i in range(0,data[MSG_LEN_INDEX]-0x06):
          extra += '{:02x} '.format(data[DATA_START_INDEX+i])
  elif data[OPCODE_INDEX] == COMMON_NACK_OPCODE:
    s += 'common_nack'
  s += ' hw_id:0x{:04x}'.format(\
   (data[HWID_MSB_INDEX]<<8)|(data[HWID_LSB_INDEX]<<0)\
  )
  s += ' msg_id:0x{:04x}'.format(\
   (data[MSG_ID_MSB_INDEX]<<8)|(data[MSG_ID_LSB_INDEX]<<0)\
  )
  s += ' src_id:0x{:01x}'.format((data[DEST_ID_INDEX]>>4)&0x0f)
  s += '('+dest_id_to_str((data[DEST_ID_INDEX]>>4)&0x0f)+')'
  s += ' dst_id:0x{:01x}'.format((data[DEST_ID_INDEX]>>0)&0x0f)
  s += '('+dest_id_to_str((data[DEST_ID_INDEX]>>0)&0x0f)+')'
  s += extra
  return s

# classes

## Command for transmitting
# TODO: a "valid" state variable that indicates whether data is a valid command
class TxCmd:
  def __init__(self, opcode, hw_id, msg_id, src, dst):
    self.data = [0x00]*CMD_MAX_LEN
    self.data[START_BYTE_0_INDEX] = START_BYTE_0
    self.data[START_BYTE_1_INDEX] = START_BYTE_1
    self.data[HWID_LSB_INDEX]     = (hw_id  >> 0) & 0xff
    self.data[HWID_MSB_INDEX]     = (hw_id  >> 8) & 0xff
    self.data[MSG_ID_LSB_INDEX]   = (msg_id >> 0) & 0xff
    self.data[MSG_ID_MSB_INDEX]   = (msg_id >> 8) & 0xff
    self.data[DEST_ID_INDEX]      = (src << 4) | (dst << 0)
    self.data[OPCODE_INDEX]       = opcode
    if self.data[OPCODE_INDEX] == APP_GET_TELEM_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == APP_GET_TIME_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == APP_REBOOT_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == APP_SET_TIME_OPCODE:
      self.data[MSG_LEN_INDEX]      = 0x0e
      self.data[DATA_START_INDEX+0] = 0x00
      self.data[DATA_START_INDEX+1] = 0x00
      self.data[DATA_START_INDEX+2] = 0x00
      self.data[DATA_START_INDEX+3] = 0x00
      self.data[DATA_START_INDEX+4] = 0x00
      self.data[DATA_START_INDEX+5] = 0x00
      self.data[DATA_START_INDEX+6] = 0x00
      self.data[DATA_START_INDEX+7] = 0x00
    elif self.data[OPCODE_INDEX] == APP_TELEM_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x54
      for i in range(0,0x54-0x06):
        self.data[DATA_START_INDEX+i] = 0x00
    elif self.data[OPCODE_INDEX] == BOOTLOADER_ACK_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == BOOTLOADER_ERASE_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == BOOTLOADER_JUMP_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == BOOTLOADER_NACK_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == BOOTLOADER_PING_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == BOOTLOADER_WRITE_PAGE_OPCODE:
      self.data[MSG_LEN_INDEX]    = 0x07
      self.data[DATA_START_INDEX] = 0x00
    elif self.data[OPCODE_INDEX] == COMMON_ACK_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == COMMON_ASCII_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == COMMON_DATA_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
    elif self.data[OPCODE_INDEX] == COMMON_NACK_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06
    else:
      self.data[MSG_LEN_INDEX] = 0x06

  def app_reboot(self, delay):
    if self.data[OPCODE_INDEX] == APP_REBOOT_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x0a
      b0 = (delay >>  0) & 0xff # LSB
      b1 = (delay >>  8) & 0xff
      b2 = (delay >> 16) & 0xff
      b3 = (delay >> 24) & 0xff # MSB
      self.data[DATA_START_INDEX+0] = b0
      self.data[DATA_START_INDEX+1] = b1
      self.data[DATA_START_INDEX+2] = b2
      self.data[DATA_START_INDEX+3] = b3

  def app_set_time(self, sec, ns):
    if self.data[OPCODE_INDEX] == APP_SET_TIME_OPCODE:
      s0 = (sec >>  0) & 0xff # LSB
      s1 = (sec >>  8) & 0xff
      s2 = (sec >> 16) & 0xff
      s3 = (sec >> 24) & 0xff # MSB
      n0 = ( ns >>  0) & 0xff # LSB
      n1 = ( ns >>  8) & 0xff
      n2 = ( ns >> 16) & 0xff
      n3 = ( ns >> 24) & 0xff # MSB
      self.data[DATA_START_INDEX+0] = s0
      self.data[DATA_START_INDEX+1] = s1
      self.data[DATA_START_INDEX+2] = s2
      self.data[DATA_START_INDEX+3] = s3
      self.data[DATA_START_INDEX+4] = n0
      self.data[DATA_START_INDEX+5] = n1
      self.data[DATA_START_INDEX+6] = n2
      self.data[DATA_START_INDEX+7] = n3

  def app_telem(self, telem):
    if self.data[OPCODE_INDEX] == APP_TELEM_OPCODE and len(telem)==78:
      for i in range(0,len(telem)):
        self.data[DATA_START_INDEX+i] = telem[i]

  def bootloader_ack(self, reason):
    if self.data[OPCODE_INDEX] == BOOTLOADER_ACK_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x07
      self.data[DATA_START_INDEX] = reason

  def bootloader_erase(self, status):
    if self.data[OPCODE_INDEX] == BOOTLOADER_ERASE_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x07
      self.data[DATA_START_INDEX] = status

  def bootloader_write_page(self, page_number, page_data=[]):
    if self.data[OPCODE_INDEX] == BOOTLOADER_WRITE_PAGE_OPCODE:
      self.data[DATA_START_INDEX] = page_number
      if len(page_data)==128:
        self.data[MSG_LEN_INDEX] = 0x87
        for i in range(0,len(page_data)):
          self.data[DATA_START_INDEX+1+i] = page_data[i]

  def common_ascii(self, ascii):
    if self.data[OPCODE_INDEX] == COMMON_ASCII_OPCODE:
      if len(ascii)<=249:
        self.data[MSG_LEN_INDEX] = 0x06+len(ascii)
        for i in range(0,len(ascii)):
          self.data[DATA_START_INDEX+i] = ord(ascii[i])
  
  def common_data(self, data):
    if self.data[OPCODE_INDEX] == COMMON_DATA_OPCODE:
      self.data[MSG_LEN_INDEX] = 0x06+len(data)
      for i in range(0,len(data),2):
          num = data[i]
          byte_arr = num.to_bytes(2, 'big')
          self.data[DATA_START_INDEX+i] = byte_arr[1]
          self.data[DATA_START_INDEX+i+1] = byte_arr[0]
    
  def get_byte_count(self):
    return self.data[MSG_LEN_INDEX]+0x03

  def clear(self):
    self.data = [0x00]*CMD_MAX_LEN

  def __str__(self):
    return cmd_bytes_to_str(self.data)

## Buffer for received TAOLST commands
class RxCmdBuff:
  def __init__(self):
    self.state = RxCmdBuffState.START_BYTE_0
    self.start_index = 0
    self.end_index = 0
    self.data = [0x00]*CMD_MAX_LEN

  def clear(self):
    self.state = RxCmdBuffState.START_BYTE_0
    self.start_index = 0
    self.end_index = 0
    self.data = [0x00]*CMD_MAX_LEN

  def append_byte(self, b):
    if self.state == RxCmdBuffState.START_BYTE_0:
      if b==START_BYTE_0:
        self.data[START_BYTE_0_INDEX] = b
        self.state = RxCmdBuffState.START_BYTE_1
    elif self.state == RxCmdBuffState.START_BYTE_1:
      if b==START_BYTE_1:
        self.data[START_BYTE_1_INDEX] = b
        self.state = RxCmdBuffState.MSG_LEN
      else:
        self.clear()
    elif self.state == RxCmdBuffState.MSG_LEN:
      if 0x06 <= b and b <= 0xff:
        self.data[MSG_LEN_INDEX] = b
        self.start_index = 0x09
        self.end_index = b+0x03
        self.state = RxCmdBuffState.HWID_LSB
      else:
        self.clear()
    elif self.state == RxCmdBuffState.HWID_LSB:
      self.data[HWID_LSB_INDEX] = b
      self.state = RxCmdBuffState.HWID_MSB
    elif self.state == RxCmdBuffState.HWID_MSB:
      self.data[HWID_MSB_INDEX] = b
      self.state = RxCmdBuffState.MSG_ID_LSB
    elif self.state == RxCmdBuffState.MSG_ID_LSB:
      self.data[MSG_ID_LSB_INDEX] = b
      self.state = RxCmdBuffState.MSG_ID_MSB
    elif self.state == RxCmdBuffState.MSG_ID_MSB:
      self.data[MSG_ID_MSB_INDEX] = b
      self.state = RxCmdBuffState.DEST_ID
    elif self.state == RxCmdBuffState.DEST_ID:
      self.data[DEST_ID_INDEX] = b
      self.state = RxCmdBuffState.OPCODE
    elif self.state == RxCmdBuffState.OPCODE:
      self.data[OPCODE_INDEX] = b
      if self.start_index < self.end_index:
        self.state = RxCmdBuffState.DATA
      else:
        self.state = RxCmdBuffState.COMPLETE
    elif self.state == RxCmdBuffState.DATA:
      if self.start_index < self.end_index:
        self.data[self.start_index] = b
        self.start_index += 1
        if self.start_index == self.end_index:
          self.state = RxCmdBuffState.COMPLETE
      else:
        self.state = RxCmdBuffState.COMPLETE
    elif self.state == RxCmdBuffState.COMPLETE:
      pass

  def __str__(self):
    if self.state == RxCmdBuffState.COMPLETE:
      return cmd_bytes_to_str(self.data)
    else:
      pass

## Buffer for transmitted TAOLST commands
class TxCmdBuff:
  def __init__(self):
    self.empty = True
    self.start_index = 0
    self.end_index = 0
    self.data = [0x00]*CMD_MAX_LEN

  def clear(self):
    self.empty = True
    self.start_index = 0
    self.end_index = 0
    self.data = [0x00]*CMD_MAX_LEN

  def generate_reply(self, rx_cmd_buff):
    if rx_cmd_buff.state==RxCmdBuffState.COMPLETE and self.empty:
      self.data[START_BYTE_0_INDEX] = START_BYTE_0
      self.data[START_BYTE_1_INDEX] = START_BYTE_1
      self.data[HWID_LSB_INDEX] = rx_cmd_buff.data[HWID_LSB_INDEX]
      self.data[HWID_MSB_INDEX] = rx_cmd_buff.data[HWID_MSB_INDEX]
      self.data[MSG_ID_LSB_INDEX] = rx_cmd_buff.data[MSG_ID_LSB_INDEX]
      self.data[MSG_ID_MSB_INDEX] = rx_cmd_buff.data[MSG_ID_MSB_INDEX]
      self.data[DEST_ID_INDEX] = \
       (0x0f & rx_cmd_buff.data[DEST_ID_INDEX]) << 4 | \
       (0xf0 & rx_cmd_buff.data[DEST_ID_INDEX]) >> 4
      if rx_cmd_buff.data[OPCODE_INDEX] == APP_GET_TELEM_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x54
        self.data[OPCODE_INDEX] = APP_TELEM_OPCODE
        for i in range(0,self.data[MSG_LEN_INDEX]-0x06):
          self.data[DATA_START_INDEX+i] = 0x00
      elif rx_cmd_buff.data[OPCODE_INDEX] == APP_GET_TIME_OPCODE:
        td  = datetime.datetime.now(tz=datetime.timezone.utc) - J2000
        sec = math.floor(td.total_seconds())
        ns  = td.microseconds * 1000
        sec_bytes = bytearray(sec.to_bytes(4,'little'))
        ns_bytes  = bytearray( ns.to_bytes(4,"little"))
        self.data[MSG_LEN_INDEX] = 0x0e
        self.data[OPCODE_INDEX] = APP_SET_TIME_OPCODE
        self.data[DATA_START_INDEX+0] = sec_bytes[0]
        self.data[DATA_START_INDEX+1] = sec_bytes[1]
        self.data[DATA_START_INDEX+2] = sec_bytes[2]
        self.data[DATA_START_INDEX+3] = sec_bytes[3]
        self.data[DATA_START_INDEX+4] =  ns_bytes[0]
        self.data[DATA_START_INDEX+5] =  ns_bytes[1]
        self.data[DATA_START_INDEX+6] =  ns_bytes[2]
        self.data[DATA_START_INDEX+7] =  ns_bytes[3]
      elif rx_cmd_buff.data[OPCODE_INDEX] == APP_REBOOT_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == APP_SET_TIME_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == APP_TELEM_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_ACK_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_ERASE_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_NACK_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_PING_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_WRITE_PAGE_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_JUMP_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == COMMON_ACK_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_ACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == COMMON_ASCII_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE
      elif rx_cmd_buff.data[OPCODE_INDEX] == COMMON_NACK_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE

  def __str__(self):
    return cmd_bytes_to_str(self.data)

# initialize script arguments
dev = '' # serial device

# parse script arguments
if len(sys.argv)==2:
  dev = sys.argv[1]
else:
  print(\
   'Usage: '\
   'python3 test_expt_data.py '\
   '/path/to/dev'\
  )
  exit()

# Create serial object
try:
  serial_port = serial.Serial(port=dev,baudrate=115200)
except:
  print('Serial port object creation failed:')
  print('  '+dev)
  exit()

###################{#############################################################
imu_vals = [
65493, 65510, 65452,3, 65475, 8171,64623, 1501, 61415,
65498, 65511, 65446,65530, 65476, 8149,64629, 1413, 61396,
65476, 65516, 65450,65526, 65464, 8145,64601, 1443, 61464,
766, 64301, 64209,64941, 58582, 3998,63981, 6849, 64412,
57, 177, 64967,65497, 58998, 5613,64413, 6497, 63813,
3186, 3032, 2929,59886, 64298, 5486,61941, 2519, 63322,
65451, 62307, 3109,63662, 5801, 4415,64555, 64053, 63621,
62829, 1469, 64572,63313, 65163, 8207,64385, 2543, 61965,
401, 3372, 65509,59693, 63269, 6032,61713, 3681, 63262,
3455, 62117, 3903,62117, 6092, 4047,64239, 63573, 6416,
63471, 1877, 63982,63585, 63333, 7533,64569, 3517, 62188,
57257, 6080, 60227,56810, 61161, 4990,62123, 5473, 728,
62698, 3289, 57608,59832, 55070, 3813,60721, 3597, 65326,
96, 4053, 55766,54208, 2794, 8605,60683, 1649, 64720
]
'''
4309, 59451, 7891,54677, 6139, 9896,62087, 65455, 63396,
5547, 65147, 65229,405, 6886, 61606,333, 63131, 2493,
60744, 2400, 62519,62356, 7519, 4570,64533, 63667, 63862,
4375, 62324, 6509,59382, 59252, 932,60983, 987, 63807,
1014, 65185, 62757,3488, 57259, 62339,61165, 311, 63580,
689, 3352, 60068,6, 58068, 1961,60905, 697, 63709,
61422, 1548, 64142,63050, 63938, 6637,65037, 4367, 62717,
1435, 1361, 8014,57412, 62309, 2132,60549, 3965, 393,
58233, 63572, 60920,62236, 4526, 7350,64487, 65175, 62776,
63238, 3853, 65368,61247, 60933, 4269,63355, 5081, 63531,
4835, 61779, 6651,57989, 2975, 3836,61845, 64865, 64273,
59653, 9541, 59511,60059, 5484, 4912,63891, 63695, 64067,
4464, 64237, 4183,61245, 62319, 5607,63081, 3637, 62701,
5194, 65455, 64989,62492, 6543, 1427,63883, 63371, 64734,
7301, 61834, 8041,56666, 7196, 4859,61589, 64679, 64965,
2374, 64066, 7818,57715, 1283, 2576,60245, 1027, 65083,
3239, 545, 3074,57930, 364, 4595,60811, 2025, 63580,
64912, 64848, 63889,58805, 1373, 6234,62317, 2729, 62304,
16982, 2448, 16808,57225, 1375, 7023,62085, 1527, 62428,
2016, 927, 890,61246, 4256, 4581,63143, 64757, 63453,
3624, 62453, 6254,58523, 1538, 4158,61821, 65513, 63249,
715, 971, 63281,62099, 1737, 592,62845, 64483, 63680,
5526, 61986, 4935,58233, 1576, 6090,61111, 451, 63101,
3575, 63931, 1138,62815, 192, 688,62471, 64767, 63493,
4077, 3195, 1018,59030, 2404, 6045,60629, 627, 62712,
424, 64937, 175,63863, 1903, 1357,62469, 64889, 63340,
3476, 60376, 4610,59661, 1114, 3026,62309, 65393, 63025,
61244, 4493, 61317,63784, 63613, 63167,61699, 253, 63323,
2363, 62536, 3589,57861, 2798, 7805,61373, 199, 62914,
65315, 65024, 65254,57921, 2351, 4328,60987, 935, 63180,
65440, 65510, 65464,58648, 1769, 4282,60903, 981, 63061,
59695, 303, 56816,58249, 1152, 4793,61405, 2037, 63163,
65076, 64242, 64437,60943, 5641, 3117,63253, 64295, 63752,
4450, 62749, 5838,56498, 741, 4940,60033, 1441, 64395,
60479, 1722, 62273,58031, 455, 6199,61103, 2115, 63088,
5698, 61343, 5869,60069, 4369, 3753,61725, 64933, 63855,
64654, 861, 401,58080, 64663, 3915,60477, 3267, 63671,
65059, 663, 60997,58315, 3468, 5162,61941, 65221, 63369,
648, 63135, 1884,57917, 199, 4353,60419, 1751, 64032,
22717, 65032, 14461,57748, 62016, 13195,61367, 2669, 63152,
57001, 65192, 57551,54144, 1920, 9294,62451, 2657, 62737,
49694, 62904, 54163,58852, 4453, 5979,62009, 1443, 62977,
2171, 63875, 72,60189, 9586, 1107,62617, 1275, 62676,
53673, 62036, 56389,59658, 582, 6130,62471, 1261, 62713,
58874, 63817, 62603,60629, 1410, 3815,62049, 64279, 63996,
182, 2118, 716,59449, 2968, 3456,62857, 3753, 63065,
53704, 59990, 53252,58083, 1080, 6938,61803, 2427, 62803,
4790, 3916, 7754,59335, 6759, 695,62209, 2653, 62868,
59070, 61046, 55518,58662, 65030, 5118,61793, 2745, 62821,
7130, 4740, 10478,56904, 58675, 11979,61231, 1325, 63118,
64288, 63419, 61105,59898, 64137, 4756,62003, 3155, 63003,
61369, 61274, 63672,59712, 34, 3723,61661, 369, 63298,
54753, 2837, 52903,55886, 260, 8058,62361, 3923, 63344,
4541, 56926, 6156,64055, 65227, 65483,62777, 64129, 64184,
53141, 4406, 53990,59018, 4483, 7399,62913, 115, 63165,
13512, 60718, 12366,61260, 62475, 3415,61337, 3575, 63679,
65476, 65515, 65440,65482, 65390, 8163,64891, 2257, 60275
]
'''

# Set up test support variables
msgid = 0x0000
rx_cmd_buff = RxCmdBuff()

# 1. Basic test
cmd = TxCmd(COMMON_ACK_OPCODE, HWID, msgid, SRC, DST)
byte_i = 0
while rx_cmd_buff.state != RxCmdBuffState.COMPLETE:
  if byte_i < cmd.get_byte_count():
    serial_port.write(cmd.data[byte_i].to_bytes(1, byteorder='big'))
    byte_i += 1
  if serial_port.in_waiting>0:
    bytes = serial_port.read(1)
    for b in bytes:
      rx_cmd_buff.append_byte(b)
print('txcmd: '+str(cmd))
print('reply: '+str(rx_cmd_buff)+'\n')
cmd.clear()
rx_cmd_buff.clear()
msgid += 1
time.sleep(1.0)

# 2. Periodic bootloader ping
for i in range(0,5):
  cmd = TxCmd(BOOTLOADER_PING_OPCODE, HWID, msgid, SRC, DST)
  byte_i = 0
  while rx_cmd_buff.state != RxCmdBuffState.COMPLETE:
    if byte_i < cmd.get_byte_count():
      serial_port.write(cmd.data[byte_i].to_bytes(1, byteorder='big'))
      byte_i += 1
    if serial_port.in_waiting>0:
      bytes = serial_port.read(1)
      for b in bytes:
        rx_cmd_buff.append_byte(b)
  print('txcmd: '+str(cmd))
  print('reply: '+str(rx_cmd_buff)+'\n')
  cmd.clear()
  rx_cmd_buff.clear()
  msgid += 1
  time.sleep(1.0)

# 3. Bootloader jump
cmd = TxCmd(BOOTLOADER_JUMP_OPCODE, HWID, msgid, SRC, DST)
byte_i = 0
while rx_cmd_buff.state != RxCmdBuffState.COMPLETE:
  if byte_i < cmd.get_byte_count():
    serial_port.write(cmd.data[byte_i].to_bytes(1, byteorder='big'))
    byte_i += 1
  if serial_port.in_waiting>0:
    bytes = serial_port.read(1)
    for b in bytes:
      rx_cmd_buff.append_byte(b)
print('txcmd: '+str(cmd))
print('reply: '+str(rx_cmd_buff)+'\n')
cmd.clear()
rx_cmd_buff.clear()
msgid += 1
time.sleep(1.0)

# 4. Basic test after jump
cmd = TxCmd(COMMON_ACK_OPCODE, HWID, msgid, SRC, DST)
byte_i = 0
while rx_cmd_buff.state != RxCmdBuffState.COMPLETE:
  if byte_i < cmd.get_byte_count():
    serial_port.write(cmd.data[byte_i].to_bytes(1, byteorder='big'))
    byte_i += 1
  if serial_port.in_waiting>0:
    bytes = serial_port.read(1)
    for b in bytes:
      rx_cmd_buff.append_byte(b)
print('txcmd: '+str(cmd))
print('reply: '+str(rx_cmd_buff)+'\n')
cmd.clear()
rx_cmd_buff.clear()
msgid += 1
time.sleep(1.0)

#common_data command test
cmd = TxCmd(COMMON_DATA_OPCODE, HWID, msgid, SRC, DST)
cmd.common_data(imu_vals)
byte_i = 0
while rx_cmd_buff.state != RxCmdBuffState.COMPLETE:
  if byte_i < cmd.get_byte_count():
    serial_port.write(cmd.data[byte_i].to_bytes(1, byteorder='big'))
    byte_i += 1
  if serial_port.in_waiting>0:
    bytes = serial_port.read(1)
    for b in bytes:
      rx_cmd_buff.append_byte(b)
print('txcmd: '+str(cmd))
print('reply: '+str(rx_cmd_buff)+'\n')
cmd.clear()
rx_cmd_buff.clear()
msgid += 1
time.sleep(1.0)

