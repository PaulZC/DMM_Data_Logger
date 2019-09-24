## DMM Data Logger
## Logs data from the BOLYFA 117 DMM (via USB serial)

## Adapted from https://github.com/inflex/BSIDE-ADM20

import serial
import time
from sys import platform

class DMMport(object):

    def __init__(self):
        self.serList = [None] * 22
        self.date_str = ''
        self.time_str = ''
        self.val_str = ''
        self.units_str = ''
        self.bar_str = ''
        self.csv_str = ',,,,\n'
        self.filename = ''

    def openSerial(self):
        # Get the serial port name
        if platform.startswith('linux'):
            # linux
            defcom = '/dev/ttyACM0'
        elif platform.startswith('darwin'):
            # OS X
            defcom = '/dev/tty.usbmodem'
        elif platform.startswith('win'):
            # Windows...
            defcom = 'COM1'
        else:
            defcom = 'COM1'

        # Ask the user to confirm the serial port name
        com_port = raw_input('Which serial port do you want to use (default '+defcom+')? ')
        if com_port == '': com_port = defcom
        print

        # Open port
        try:
            self.ser = serial.Serial(com_port, 2400, timeout=0.1)
        except:
            raise NameError('COULD NOT OPEN SERIAL PORT!')

        self.ser.flushInput() # Flush RX buffer

    def openLogFile(self):
        start_time = time.time() # Get the time
        tn = time.localtime(start_time) # Extract the time and date as strings
        date_str = str(tn[0])+str(tn[1]).zfill(2)+str(tn[2]).zfill(2)
        time_str = str(tn[3]).zfill(2)+str(tn[4]).zfill(2)+str(tn[5]).zfill(2)
        # Assemble the file name using the date, time and port name
        self.filename = 'DMM_Log_' + date_str + '_' + time_str + '.csv'

        try:
            self.fp = open(self.filename, 'w') # Create / clear the file
        except:
            raise NameError('COULD NOT OPEN LOG FILE!')

        print 'Logging data to', self.filename
        print
        print 'Press CTRL+C to stop logging'
        print

        self.fp.write('DMM_Log\n') # Write the file header
        self.fp.write('DATE,TIME,VALUE,UNITS,BAR,Extras\n')
        self.fp.write('\n')

    def closePort(self):
        self.ser.close() # Close the serial port

    def closeLogFile(self):
        self.fp.close() # Close the file

    def readByte(self):
        ''' Read one byte from the serial port, store it in serList and return true if a complete packet has been received '''
        rx = self.ser.read(1) # Try to read one byte from serial port
        if rx != '': # If a byte was received
            self.serList = self.serList[1:] + [ord(rx)] # Shuffle serList and add the byte to the end
            if (self.serList[0] == 0xAA) and (self.serList[1] == 0x55) \
               and (self.serList[2] == 0x52) and (self.serList[3] == 0x24) \
               and (self.serList[4] == 0x01) and (self.serList[5] == 0x10): # Is the header valid?
                return True
            else:
                return False
        else:
            return False

    def processDigit(self, digit):
        ''' Convert seven segment data into a char '''
        # Segment bit order is: (msb) DP E G F D C B A (lsb)
        if digit & 0x7F == 0x5F: return '0'
        elif digit & 0x7F == 0x06: return '1'
        elif digit & 0x7F == 0x6B: return '2'
        elif digit & 0x7F == 0x2F: return '3'
        elif digit & 0x7F == 0x36: return '4'
        elif digit & 0x7F == 0x3D: return '5'
        elif digit & 0x7F == 0x7D: return '6'
        elif digit & 0x7F == 0x07: return '7'
        elif digit & 0x7F == 0x7F: return '8'
        elif digit & 0x7F == 0x3F: return '9'
        elif digit & 0x7F == 0x79: return 'E'
        elif digit & 0x7F == 0x58: return 'L'
        else: return ''

    def processDP(self, digit):
        ''' Process the decimal point '''
        if digit & 0x80: return '.'
        else: return ''

    def countBits(self, byte):
        ''' Count the number of set bits (1's) in the byte '''
        binary = bin(byte)
        setBits = [ones for ones in binary[2:] if ones=='1']
        return len(setBits)

    def processData(self):
        # Still to find: LOW_BATT, HOLD, NCV, Wait, and the 'clock' symbol in the top left corner
        
        # Process the value
        if (self.serList[10]&0x08): self.val_str = '-'
        else: self.val_str = ''
        self.val_str = self.val_str + self.processDigit(self.serList[9])
        for a in self.serList[8:5:-1]:
            self.val_str = self.val_str + self.processDP(a)
            self.val_str = self.val_str + self.processDigit(a)

        # Process the units
        self.units_str = ''
        if (self.serList[21] & 0x20): self.units_str = self.units_str + 'k' # kilo
        if (self.serList[21] & 0x10): self.units_str = self.units_str + 'M' # Mega
        if (self.serList[21] & 0x02): self.units_str = self.units_str + 'm' # milli
        if (self.serList[21] & 0x01): self.units_str = self.units_str + 'u' # micro
        if (self.serList[21] & 0x80): self.units_str = self.units_str + 'Hz'
        if (self.serList[21] & 0x40): self.units_str = self.units_str + 'R' # Ohm
        if (self.serList[21] & 0x08): self.units_str = self.units_str + 'V'
        if (self.serList[21] & 0x04): self.units_str = self.units_str + 'A'
        if (self.serList[20] & 0x20): self.units_str = self.units_str + 'u' # micro
        if (self.serList[20] & 0x40): self.units_str = self.units_str + 'n' # nano
        if (self.serList[20] & 0x80): self.units_str = self.units_str + 'F' # Farads
        if (self.serList[20] & 0x02): self.units_str = self.units_str + 'oF' # degrees F
        if (self.serList[20] & 0x01): self.units_str = self.units_str + 'oC' # degrees C
        if (self.serList[19] & 0x20): self.units_str = self.units_str + '%'
        if (self.serList[19] & 0x40): self.units_str = self.units_str + 'hFE'
        if (self.serList[10] & 0x04): self.units_str = self.units_str + ' DC'
        if (self.serList[10] & 0x02): self.units_str = self.units_str + ' AC'

        # Process the extras
        # Note: the bar graph legend is self.serList[10] & 0x20
        extra_str = ''
        if (self.serList[19] & 0x01): extra_str = extra_str + ',USB'
        if (self.serList[18] & 0x20): extra_str = extra_str + ',AUTO'
        if (self.serList[18] & 0x80): extra_str = extra_str + ',REL'
        
        if (self.serList[19] & 0x0A): extra_str = extra_str + ',' # If either MAX or MIN is displayed
        if (self.serList[19] & 0x02): extra_str = extra_str + 'MAX'
        if (self.serList[19] & 0x04): extra_str = extra_str + '-'
        if (self.serList[19] & 0x08): extra_str = extra_str + 'MIN'

        if (self.serList[10] & 0x40): extra_str = extra_str + ',CONT' # Continuity beep
        if (self.serList[10] & 0x01): extra_str = extra_str + ',DIODE'

        # Process the bar graph
        # The bar graph maximum is 60
        bars = 0
        for a in self.serList[11:18]:
            bars = bars + self.countBits(a)
        bars = bars + self.countBits(self.serList[18] & 0x0F)
        self.bar_str = str(bars)

        # Get the time and date
        t = time.time()
        tn = time.localtime(t) # Extract the time and date as strings
        millis = int(t * 1000) - (int(t) * 1000) # Calculate the milliseconds
        self.date_str = str(tn[0])+'/'+str(tn[1]).zfill(2)+'/'+str(tn[2]).zfill(2)
        self.time_str = str(tn[3]).zfill(2)+':'+str(tn[4]).zfill(2)+':'+str(tn[5]).zfill(2)+'.%03i'%millis

        # Form the CSV string
        self.csv_str = self.date_str + ',' + self.time_str + ',' + self.val_str + \
                       ',' + self.units_str + ',' + self.bar_str + extra_str + '\n'

    def writeData(self):
        self.fp.write(self.csv_str)

if __name__ == '__main__':
    try:
        print 'DMM Data Logger'
        print
        
        dp = DMMport() # Init DMMport
        dp.openSerial() # Open the serial port
        dp.openLogFile() # Open the log file

        while True:
            if dp.readByte(): # Read a serial byte and check if a preamble has been detected
                dp.processData() # If it has, process the data,
                dp.writeData() # write it to the log file
                print dp.csv_str # and print it to the screen

    except KeyboardInterrupt:
        print
        print 'CTRL+C received...'
        print

    finally:
        try:
            dp.closePort() # Close the serial port
        except:
            pass
        try:
            dp.closeLogFile() # Close the file
        except:
            pass


