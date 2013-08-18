'''
Created on Jul 12, 2013
Last Modified on Aug 17, 2013

@author: Rohit
'''

import sys                             # for command line arguments 
import serial                         # for serial port access
import re                               # regex
from math import *              # for floor() and ceil()
import time                           # for usleep() replacement

''' 
determine OS 
$Os = $^O;                        # ^O is contains operating system value

use Time::HiRes(usleep);
use POSIX qw(ceil floor);

if($Os == "MSWin32"){
        use Win32::SerialPort;
}else{
        #Use Device::SerialPort for linux
        print "Only Win32 Operating Systems supported";
}
'''

usleep = lambda x: time.sleep( x / 1000000.0 ) #usleep() derivation from time.sleep()

LineNumber = 0
TdiLength = 0

portName = sys.argv[1]          # "COM45"
FileName = sys.argv[2]                 #"s.svf"

#JTAG_STATES==> Changed TL_RESET state to RESET
JTAG_STATES = {           'RESET' :  0x0,
                                       'IDLE' : 0x1,
                                       'DRSELECT' : 0x9,
                                       'DRCAPTURE' : 0xa,
                                       'DRSHIFT' : 0xb,
                                       'DREXIT1' : 0xc,
                                       'DRPAUSE' : 0xd,
                                       'DREXIT2' : 0xe,
                                       'DRUPDATE' : 0xf,
                                       'IRSELECT' : 0x2,
                                       'IRCAPTURE' : 0x3,
                                       'IRSHIFT' : 0x4,
                                       'IREXIT1' : 0x5,
                                       'IRPAUSE' : 0x6,
                                       'IREXIT2' : 0x7,
                                       'IRUPDATE' : 0x8} 

#print JTAG_STATES

def OpenPort( strPortName ):
        ''' '''
        port = serial.Serial()
        port.baudrate = 9600
        port.parity = serial.PARITY_NONE
        port.bytesize = serial.EIGHTBITS
        port.stopbits = serial.STOPBITS_ONE 
        port.timeout = 5
        port.port = strPortName
        port.open()
        return port

        '''
        $port -> parity( "none" )
        $port -> databits( 8 )
        $port -> stopbits( 1 )
        $port -> handshake( "none" )
        $port -> buffers( 4096, 4096 )
        $port -> read_interval( 100 )  
        $port -> read_char_time( 5 )
        $port -> read_const_time( 100 )
        $port -> write_char_time( 5 )
        $port -> write_const_time( 100 )
        $port -> lookclear()'''
        
        return port

def SendAndReceive( port = None , SendData = None, SendLen = None, ReceiveData = None, ReceiveLen = None ):
        ''' '''
        if port is None:
                print "NULL port provided"
                return
        
        port.flush()            # $port->lookclear();
        print "To Write: " + SendData
        BytesWritten = port.write( SendData )
        if BytesWritten != SendLen:
                return 0
       
        ReceiveData = port.read( ReceiveLen )
        print "Read Data: " + ReceiveData
		
        count = len( ReceiveData )
        if count != ReceiveLen:
                return 0
        
		
        if re.search( "\?", ReceiveData ):
                print "Chipmunk returned error at line number $LineNumber\n"
                port.close()
                exit()
        return count, ReceiveData
        
def EchoOn( port = None ):
        ''' '''
        SendAndReceive( port, "echo on\r", 9, None, None )
        
def EchoOff( port = None ):
        ''' '''
        SendAndReceive( port, "echo off\r", 10, None, None )
        port.flush()
        
def GetVersion( _port = None ):
        ''' '''
        port = _port
        tmpString = ""
        
        len, tmpString = SendAndReceive( port, "ver\r", 4, tmpString, 8 )
        if  len:
                return tmpString
        return None

def Enddr( _port, _state ):
        ''' '''
        port = _port
        state = _state
        tmpString = ""
        len = 0
        tmpString = SendAndReceive( port, "enddr " + hex( state )[2:] + "\r", 8, tmpString, 8 )
        print tmpString
        return tmpString
        
def Endir( _port, _state ):
        ''' '''
        port = _port
        state = _state
        tmpString = ""
        len = 0
        tmpString = SendAndReceive( port, "endir " + hex( state )[2:] + "\r", 8, tmpString, 8 )
        print tmpString
        return tmpString
 
def Reset( _port ):
        ''' '''
        port = _port
        tmpString = ""
        len = 0
        tmpString = SendAndReceive( port, "reset\r", 6, tmpString, 0 )
        print tmpString
        return tmpString
        
def TapAdvance( _port, _tms ):
        ''' '''
        port = _port
        tmpString = ""
        tms = _tms
        len = 0
        
        tmpString = SendAndReceive( port, "a " + hex( tms )[2:] + "\r", 4, tmpString, 2 )
        print tmpString
        return tmpString
        
def GoToState( _port, _state ):
        ''' '''
        port = _port
        state = _state
        tmpString = ""
        len = 0
        tmpString = SendAndReceive( port, "g " + hex( state )[2:] + "\r", 4, tmpString, 2 )
        print tmpString
        return tmpString
         
def GetState( _port ):
        ''' '''
        port = _port
        tmpString = ""
        len = 0
        len, tmpString = SendAndReceive( port, "q\r", 2 , tmpString, 1 )
        if  len != 0:
                return tmpString
        return None
       
def SelectIR( _port ):
        ''' '''
        port = _port
        tmpString = ""
        state = None
        
        SendAndReceive( port, "i\r", 2 , tmpString, 1 )
        state = GetState( port )
        if state != "4":
                GoToState( port, 0 )
                SendAndReceive( port, "i\r", 2 , tmpString, 1 )
        
        
        state = GetState( port )
        return state
        
def SelectDR( _port ):
        ''' '''
        port = _port
        tmpString = ""
        state = None
        
        SendAndReceive( port, "d\r", 2 , tmpString, 1 )
        state = GetState( port )
        if state != "B":
                GoToState( port, 0 )
                SendAndReceive( port, "d\r", 2 , tmpString, 1 )
                
        
        state = GetState( port )
        return state

def Scan( _port, _tdi, _tdilen, _exitstate ):
        ''' '''
        port = _port
        Tdi = _tdi
        TdiLen = int(_tdilen)
        ExitState = _exitstate
        tmpString = ""
        len = 0
        if TdiLen > 32:
                return None
        
        if  ExitState == 0 :
                len, tmpString = SendAndReceive( port, "s " + substr( Tdi, 0, int( ceil( TdiLen / 4.0 ) ) ) + " " + ( "%02x" % TdiLen ) + "\r", int( ceil( TdiLen / 4.0 ) ) + 6, tmpString, int( ceil( TdiLen / 4.0 ) ) )
                if len:
                        return tmpString
                else:
                        return None
        else:
                print "hulla", substr( Tdi, 0, int( ceil( TdiLen / 4.0 ) ) )
                len, tmpString = SendAndReceive( port, "x " + substr( Tdi, 0, int( ceil( TdiLen / 4.0 ) ) ) + " " + ( "%02x" % TdiLen ) + "\r", int( ceil( TdiLen / 4.0 ) ) + 6, tmpString, int( ceil( TdiLen / 4.0 ) ) ) 
                if len:
                        return tmpString
                else:
                        None        

def Runtest( _port, _cycles ):
        ''' '''
        port = _port
        cycles = int(re.sub("TCK", "", _cycles))
        tmpString = ""
        
        SendAndReceive( port, "r " + ( "%x" % cycles ) + "\r", 4 , tmpString, 0 )
        #Wait a ltille bit before issuing next command
        usleep( cycles / 2 )
        
def RunSVF( _portName, _FileName ):
        port = _portName
        FileName = _FileName
        portName = port.port
        
        print "Processing SVF, please wait:\nPort: " + portName + "\nFilename: " + FileName + "\n\n****************\n"
        
        SVF = open( FileName, 'r' )
        SVF_enumerate = enumerate( SVF )
        
        for i, line in SVF_enumerate:
                #print str(i+1) +" : " + line,
                #print "\n\n____________________________________\nProcessing line " + str( i + 1 ) + "\r\nLine: " + line
                #time.sleep(0.005)
                #Check and strip any comments
                comment_found = re.search( "\/\/", line )
                if comment_found:
                        #print "COMMENT FOUND!!"
                        line = line[0:comment_found.start()]  #line without comment part
                        #print "Line is : " + line
                
                #strip extra white spaces
                line = re.sub( r"\s+", " ", line )
                #print "Line w/o whitespace: " + line + "hello"
                
                if re.search( "TRST", line, re.IGNORECASE ):
                        #Ignore
                        print "found /TRST/i...ignored"
                
                elif re.search( "ENDIR", line, re.IGNORECASE ):
                        if not re.search( ";", line ):
                                print "Error at line no. " + ( i + 1 )
                                return
                        
                        #print "EndirHandler(" + port + ", " + line + ")"
                        EndirHandler( port , line )
                
                elif re.search( "ENDDR", line, re.IGNORECASE ):
                        if not re.search( ";", line ):
                                print "Error at line no. " + ( i + 1 )
                                return
                        
                        #print "EnddrHandler(" + port + ", " + line + ")"
                        EnddrHandler( port, line )
                                
                elif re.search( "STATE", line, re.IGNORECASE ):
                        if not re.search( ";", line ):
                                print "Error at line no. " + ( i + 1 )
                                return
                        
                        #print "StateHandler(" + port + ", " + line + ")"
                        StateHandler( port, line )
                                
                elif re.search( "RUNTEST", line, re.IGNORECASE ):
                        if not re.search( ";", line ):
                                print "Error at line no. " + ( i + 1 )
                                return
                        
                        #print "RuntestHandler(" + port + ", " + line + ")"
                        RuntestHandler( port, line )

                elif re.search( "SIR", line, re.IGNORECASE ):
                        #if not re.search(";", line):
                        #        print "Error at line no. " + (i+1)
                        #        return
                        
                        #print "SirHandler(" + port + ", " + line + ")"
                        SirHandler( port, line )

                elif re.search( "SDR", line, re.IGNORECASE ):
                        
                        #Sometimes SDR TDI data can be very long spanning multiple lines
                        end = 0
                        while not end:
                                if re.search( "\)", line ):
                                        #print "SdrHandler(" + port + ", " + line + ", 1)"
                                        SdrHandler( port, line, 1 )
                                        end = 1
                                else:
                                        #print "SdrHandler(" + port + ", " + line + ", 0)"
                                        SdrHandler( port , line , 0 )
                                        i, line = SVF_enumerate.next()        #increment line, and linenumber
                                                       
        SVF.close()
        print "\nDone\n"
        return       

def SirHandler( _port, _line ):
        port = _port
        line = _line
        portName = port.port
        #print "\n\n" + portName + " -- " + line + " ||"
         
        
        #print "SelectIR(" + port + ") \n"
        SelectIR( port )
        
        regmatch = re.search( r"SIR *([0-9]*) *TDI *\(([0-9a-fA-F]+)\)", line, re.IGNORECASE )
        
        print "Scan(" + portName + ", " + regmatch.group( 2 ) + ", " + regmatch.group( 1 ) + ", 1);" 
        Scan( port, regmatch.group( 2 ), regmatch.group( 1 ), 1 )
             
def SdrHandler( _port, _line, _end ):
        port = _port
        line = _line
        end = _end
        portName = port.port
        print line
        LineLength = 0
        i = 0
        
        regmatch = re.search( r"SDR +([0-9]+)", line, re.IGNORECASE )
        if regmatch:
                TdiLength = int( regmatch.group( 1 ) )
                regmatch = re.search( r"TDI +\((.+)", line, re.IGNORECASE )
                line = regmatch.group( 1 )
        
        if end:
                regmatch = re.search( r"([0-9a-fA-F]*)\)", line, re.IGNORECASE )
                line = regmatch.group( 1 )
        
        line = re.sub( r"\s+$", "", line )
        #print "SelectDR(" + port + ");" 
        SelectDR( port )
        
        LineLength = len( line ) * 4
        #print " Print1: ",line, LineLength, TdiLength
        if LineLength > TdiLength:
                #print "Truce"
                line = substr( line, int( floor( ( LineLength - TdiLength ) / 4.0 ) ), int( LineLength / 4 ) )
                LineLength = TdiLength
        
        AdjustedLineLength = int( ceil( LineLength / 4.0 ) )
        #print " Print2: ",line, LineLength, TdiLength, AdjustedLineLength
        
        while LineLength:
                if LineLength >= 32:
                        #print "hulla"
                        i = i + 8
                        #print "Scan(" + port + ", substr(" + line + ", " + str( -i ) + ", 8) , 32, 0);"
                        print "Scan(" + portName + ", " + substr( line, -i, 8 ) + " , 32, 0);"
                        Scan( port, substr( line, -i, 8 ) , 32, 0 )
                        LineLength = LineLength - 32
                        TdiLength = TdiLength - 32
                else:
                        #print "hallooo"
                        #print "Scan(" + port + ", substr(" + line + ",-(" + \
                        #                str( AdjustedLineLength ) + ")," + str( AdjustedLineLength ) + \
                        #                " - " + str( i ) + " , " + str( LineLength ) + ", " + str( end ) + ");"
                                        
                        print "Scan(" + portName + ", " + substr( line, -AdjustedLineLength, AdjustedLineLength - i ) + \
                                        " , " + str( LineLength ) + ", " + str( end ) + ");"
                        Scan( port, substr( line, -AdjustedLineLength, AdjustedLineLength - i ) , LineLength, end )
                        LineLength = 0

def RuntestHandler( _port, _line ):
        port = _port
        line = _line
        #portName = port.port
        
        print line
        
        if not re.search( "TCK", line, re.IGNORECASE ) :
                print "Error at line no. LineNumber, only TCK is supported with RUNTEST"
        
        regmatch = re.search( r"\s+(.*)\s*;", line, re.IGNORECASE )
        #print "Runtest(" + port + ", " + regmatch.group( 1 ) + ");" 
        Runtest( port, regmatch.group( 1 ) )

def EndirHandler( _port, _line ):
        port = _port
        line = _line
        #portName = port.port

        print line
        
        regmatch = re.search( r"\s+(.*)\s*;", line, re.IGNORECASE )
        
        #print "Endir(" + port + " , " + str( JTAG_STATES[regmatch.group( 1 )] ) + ");\n"
        Endir( port , JTAG_STATES[regmatch.group( 1 )] ) 

def EnddrHandler( _port, _line ):
        port = _port
        line = _line
        #portName = port.port

        print line
        
        regmatch = re.search( r"\s+(.*)\s*;", line, re.IGNORECASE )
        
        #print "Enddr(" + port + " , " + str( JTAG_STATES[regmatch.group( 1 )] ) + ");\n"
        Enddr( port , JTAG_STATES[regmatch.group( 1 )] )

def StateHandler( _port, _line ):
        ''' '''
        port = _port
        line = _line
        #portName = port.port

        print line
        
        regmatch = re.search( r"\s+(.*)\s*;", line, re.IGNORECASE )
        
        #print "GoToState(" + port + " , " + str( JTAG_STATES[regmatch.group( 1 ).upper()] ) + ");\n"
        GoToState( port , JTAG_STATES[regmatch.group( 1 ).upper()] )

def substr( string, offset, count ):
        if offset >= 0 and count >= 0:
                return string[offset : offset + count]
        
        elif offset < 0 and count >= 0:
                offset = len( string ) + offset
                return string[offset : offset + count ]
        
        elif offset < 0 and count < 0:
                offset = len( string ) + offset
                return string[offset : len( string ) + count]
        
        elif offset >= 0 and count < 0:
                return string[offset : len( string ) + count]


#####################################

serport = OpenPort( portName )

EchoOff( serport );
RunSVF( serport, FileName ) ;

serport.close();
