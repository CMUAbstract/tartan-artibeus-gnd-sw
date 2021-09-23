# Usage: python3 demo.py /path/to/src /path/to/dst
# Parameters:
#  /path/to/src: Path to input file
#  /path/to/dst: destination directory for output file
# Output:
#  out.hex: The hex-format replies to the input commands

# import Python modules
import copy # deepcopy
import enum # Enum
import sys  # accessing script arguments
import time # Return time for app_get_time command
from datetime import datetime

################################################################################

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

MAX_DELAY = 1000
FLASH_WRITE_OK = True
TIME_SET = True
BOOT_STATE = True
J2000 = datetime(2000, 1, 1, 11, 58, 55, 816000)
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

## Converts a list of command bytes (ints) to a human-readable string
def cmd_bytes_to_str(data):
  s = ''
  if data[OPCODE_INDEX] == APP_GET_TELEM_OPCODE:
    # app_get_telem hwid msgid src dst
    s += 'app_get_telem '
    s += str(data[HWID_MSB_INDEX]) + ' '
    s += str(data[HWID_LSB_INDEX]) + ' '
    s += str(data[MSG_ID_MSB_INDEX]) + ' '
    s += str(data[MSG_ID_LSB_INDEX]) + ' '
    s += str(data[DEST_ID_INDEX]) 
  
  elif data[OPCODE_INDEX] == APP_GET_TIME_OPCODE:
    # app_get_time hwid msgid src dst
    s += 'app_get_time '
    s += str(data[HWID_MSB_INDEX]) + ' '
    s += str(data[HWID_LSB_INDEX]) + ' '
    s += str(data[MSG_ID_MSB_INDEX]) + ' '
    s += str(data[MSG_ID_LSB_INDEX]) + ' '
    s += str(data[DEST_ID_INDEX])
    
  elif data[OPCODE_INDEX] == APP_REBOOT_OPCODE:
    # app_reboot hwid msgid src dst delay_sec
    s += 'app_reboot '
    s += str(data[HWID_MSB_INDEX]) + ' '
    s += str(data[HWID_LSB_INDEX]) + ' '
    s += str(data[MSG_ID_MSB_INDEX]) + ' '
    s += str(data[MSG_ID_LSB_INDEX]) + ' '
    s += str(data[DEST_ID_INDEX]) + ' '
    
  elif data[OPCODE_INDEX] == APP_SET_TIME_OPCODE:
    # app_set_time hwid msgid src dst sec ns
    pass
  elif data[OPCODE_INDEX] == APP_TELEM_OPCODE:
    # app_telem hwid msgid src dst
    pass
  elif data[OPCODE_INDEX] == BOOTLOADER_ACK_OPCODE:
    # bootloader_ack hwid msgid src dst reason
    s += 'bootloader_ack '
    s += str(data[HWID_MSB_INDEX]) + ' '
    s += str(data[HWID_LSB_INDEX]) + ' '
    s += str(data[MSG_ID_MSB_INDEX]) + ' '
    s += str(data[MSG_ID_LSB_INDEX]) + ' '
    s += str(data[DEST_ID_INDEX]) + ' '
    s += str(data[DATA_START_INDEX])

  elif data[OPCODE_INDEX] == BOOTLOADER_ERASE_OPCODE:
    # bootloader_erase hwid msgid src dst
    s += 'bootloader_erase '
    s += str(data[HWID_MSB_INDEX]) + ' '
    s += str(data[HWID_LSB_INDEX]) + ' '
    s += str(data[MSG_ID_MSB_INDEX]) + ' '
    s += str(data[MSG_ID_LSB_INDEX]) + ' '
    s += str(data[DEST_ID_INDEX]) 

  elif data[OPCODE_INDEX] == BOOTLOADER_JUMP_OPCODE:
    # bootloader_jump hwid msgid src dst
    s += 'bootloader_jump '
    s += str(data[HWID_MSB_INDEX]) + ' '
    s += str(data[HWID_LSB_INDEX]) + ' '
    s += str(data[MSG_ID_MSB_INDEX]) + ' '
    s += str(data[MSG_ID_LSB_INDEX]) + ' '
    s += str(data[DEST_ID_INDEX])

  elif data[OPCODE_INDEX] == BOOTLOADER_NACK_OPCODE:
    # bootloader_nack hwid msgid src dst
    s += 'bootloader_nack '
    s += str(data[HWID_MSB_INDEX]) + ' '
    s += str(data[HWID_LSB_INDEX]) + ' '
    s += str(data[MSG_ID_MSB_INDEX]) + ' '
    s += str(data[MSG_ID_LSB_INDEX]) + ' '
    s += str(data[DEST_ID_INDEX])

  elif data[OPCODE_INDEX] == BOOTLOADER_PING_OPCODE:
    # bootloader_ping hwid msgid src dst
    s += 'bootloader_ping '
    s += str(data[HWID_MSB_INDEX]) + ' '
    s += str(data[HWID_LSB_INDEX]) + ' '
    s += str(data[MSG_ID_MSB_INDEX]) + ' '
    s += str(data[MSG_ID_LSB_INDEX]) + ' '
    s += str(data[DEST_ID_INDEX])

  elif data[OPCODE_INDEX] == BOOTLOADER_WRITE_PAGE_OPCODE:
    # bootloader_write_page hwid msgid src dst page_number hex_data
    pass
  elif data[OPCODE_INDEX] == COMMON_ACK_OPCODE:
    # common_ack hwid msgid src dst
    s += 'common_ack '
    s += str(data[HWID_MSB_INDEX]) + ' '
    s += str(data[HWID_LSB_INDEX]) + ' '
    s += str(data[MSG_ID_MSB_INDEX]) + ' '
    s += str(data[MSG_ID_LSB_INDEX]) + ' '
    s += str(data[DEST_ID_INDEX])

  elif data[OPCODE_INDEX] == COMMON_ASCII_OPCODE:
    # common_ascii hwid msgid src dst string
    pass
  elif data[OPCODE_INDEX] == COMMON_NACK_OPCODE:
    # common_nack hwid msgid src dst
    s += 'common_nack '
    s += str(data[HWID_MSB_INDEX]) + ' '
    s += str(data[HWID_LSB_INDEX]) + ' '
    s += str(data[MSG_ID_MSB_INDEX]) + ' '
    s += str(data[MSG_ID_LSB_INDEX]) + ' '
    s += str(data[DEST_ID_INDEX])

  return s

# classes

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
      #What is the purpose of this
      self.data[DEST_ID_INDEX] = \
       (0x0f & rx_cmd_buff.data[DEST_ID_INDEX]) << 4 | \
       (0xf0 & rx_cmd_buff.data[DEST_ID_INDEX]) >> 4
      #Not sure about length byte
      if rx_cmd_buff.data[OPCODE_INDEX] == APP_GET_TELEM_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = APP_TELEM_OPCODE

      elif rx_cmd_buff.data[OPCODE_INDEX] == APP_GET_TIME_OPCODE:
        if TIME_SET:
          dt = datetime.utcnow() - J2000
          seconds = int(dt.total_seconds())
          nanoseconds = dt.microseconds * 1000
          seconds_bytes = bytearray(seconds.to_bytes(4, 'little'))
          nanoseconds_bytes = bytearray(nanoseconds.to_bytes(4, "little"))
          self.data[MSG_LEN_INDEX] = 0x0e
          self.data[OPCODE_INDEX] = APP_SET_TIME_OPCODE
          self.data[DATA_START_INDEX] = seconds_bytes[0]
          self.data[DATA_START_INDEX+1] = seconds_bytes[1]
          self.data[DATA_START_INDEX+2] = seconds_bytes[2]
          self.data[DATA_START_INDEX+3] = seconds_bytes[3]
          self.data[DATA_START_INDEX+4] = nanoseconds_bytes[0]
          self.data[DATA_START_INDEX+5] = nanoseconds_bytes[1]
          self.data[DATA_START_INDEX+6] = nanoseconds_bytes[2]
          self.data[DATA_START_INDEX+7] = nanoseconds_bytes[3]
        else:
          self.data[MSG_LEN_INDEX] = 0x06
          self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE

      elif rx_cmd_buff.data[OPCODE_INDEX] == APP_REBOOT_OPCODE:
        #If no delay provided, then common ack immediately
        if(rx_cmd_buff.data[MSG_LEN_INDEX] == 0x06):
          self.data[MSG_LEN_INDEX] = 0x06
          self.data[OPCODE_INDEX] = COMMON_ACK_OPCODE
        else:
          delay_bytes = rx_cmd_buff.data[DATA_START_INDEX:DATA_START_INDEX+4]
          delay = \
            (delay_bytes[3] << 24) + (delay_bytes[2] << 16) + \
            (delay_bytes[1] << 8) + (delay_bytes[0])
          if (delay <= MAX_DELAY):
            self.data[MSG_LEN_INDEX] = 0x06
            self.data[OPCODE_INDEX] = COMMON_ACK_OPCODE
          else:
            self.data[MSG_LEN_INDEX] = 0x06
            self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE

      elif rx_cmd_buff.data[OPCODE_INDEX] == APP_SET_TIME_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_ACK_OPCODE

      elif rx_cmd_buff.data[OPCODE_INDEX] == APP_TELEM_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE

      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_ACK_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE

      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_ERASE_OPCODE:
        if BOOT_STATE:
          self.data[MSG_LEN_INDEX] = 0x07
          self.data[OPCODE_INDEX] = BOOTLOADER_ACK_OPCODE
          self.data[DATA_START_INDEX] = BOOTLOADER_ACK_REASON_ERASED
        else:
          self.data[MSG_LEN_INDEX] = 0x06
          self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE

      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_NACK_OPCODE:
        self.data[MSG_LEN_INDEX] = 0x06
        self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE

      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_PING_OPCODE:
        if BOOT_STATE:
          self.data[MSG_LEN_INDEX] = 0x07
          self.data[OPCODE_INDEX] = BOOTLOADER_ACK_OPCODE
          self.data[DATA_START_INDEX] = BOOTLOADER_ACK_REASON_PONG
        else:
          self.data[MSG_LEN_INDEX] = 0x06
          self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE

      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_WRITE_PAGE_OPCODE:
        if BOOT_STATE:
          if (FLASH_WRITE_OK):
            page_number = rx_cmd_buff.data[DATA_START_INDEX]
            self.data[MSG_LEN_INDEX] = 0x07
            self.data[OPCODE_INDEX] = BOOTLOADER_ACK_OPCODE
            self.data[DATA_START_INDEX] = page_number
          else:
            self.data[MSG_LEN_INDEX] = 0x06
            self.data[OPCODE_INDEX] = BOOTLOADER_NACK_OPCODE
        else:
          self.data[MSG_LEN_INDEX] = 0x06
          self.data[OPCODE_INDEX] = COMMON_NACK_OPCODE

      elif rx_cmd_buff.data[OPCODE_INDEX] == BOOTLOADER_JUMP_OPCODE:
        if BOOT_STATE:
          self.data[MSG_LEN_INDEX] = 0x07
          self.data[OPCODE_INDEX] = BOOTLOADER_ACK_OPCODE
          self.data[DATA_START_INDEX] = BOOTLOADER_ACK_REASON_JUMP
        else:
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

################################################################################

# initialize script arguments
src = '' # input file
dst = '' # output directory

# parse script arguments
if len(sys.argv)==3:
  src = sys.argv[1]
  dst = sys.argv[2]
  if dst[-1] != '/':
    dst += '/'
else:
  print(\
   'Usage: '\
   'python3 demo.py '\
   '/path/to/src /path/to/dst'\
  )
  exit()

# Read the input file
rx_cmds = []
with open(src, 'rb') as infile:
  
  rx_cmd_buff = RxCmdBuff()
  b = infile.read(1)
  while b:
    rx_cmd_buff.append_byte(int.from_bytes(b, byteorder='big'))
    if rx_cmd_buff.state == RxCmdBuffState.COMPLETE:
      print(rx_cmd_buff)
      rx_cmds.append(copy.deepcopy(rx_cmd_buff))
      rx_cmd_buff.clear()
    b = infile.read(1)

# Generate the responses

tx_cmds = []
for rx_cmd in rx_cmds:
 
  tx_cmd_buff = TxCmdBuff()
  tx_cmd_buff.generate_reply(rx_cmd)
  tx_cmds.append(copy.deepcopy(tx_cmd_buff))
  tx_cmd_buff.clear()

# Write out log file
with open(dst+'reply-'+src.split('/')[-1], 'wb') as outfile:
  for tx_cmd in tx_cmds:
    size = 0x03+tx_cmd.data[MSG_LEN_INDEX]
    outfile.write(bytearray(tx_cmd.data[0:size]))

