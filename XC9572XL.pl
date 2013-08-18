#!/usr/bin/perl

#rename this file from .txt to .pl

#TODO
#Support all commands in SVF specification
#Implement thorough error handling
#Verify TDO values. Currently hardware supports this but not implemented in this script

#Numato Lab www.numato.com, www.numato.cc
#License : http://creativecommons.org/licenses/by-sa/2.0/

# Determin operating system
$Os = $^O;

use Time::HiRes(usleep);
use POSIX qw(ceil floor);

if($Os == "MSWin32"){
	use Win32::SerialPort;
}else{
	#Use Device::SerialPort for linux
	print "Only Win32 Operating Systems supported";
}

my $LineNumber = 0;
my $TdiLength = 0;

$portName = $ARGV[0];
$FileName = $ARGV[1];

###########################################################################
#                         Chipmunk APIs                                   #
###########################################################################

%JTAG_STATES = (
	'TL_RESET' => 0x0,
	'IDLE' => 0x1,
	'DRSELECT' => 0x9,
	'DRCAPTURE' => 0xa,
	'DRSHIFT' => 0xb,
	'DREXIT1' => 0xc,
	'DRPAUSE' => 0xd,
	'DREXIT2' => 0xe,
	'DRUPDATE' => 0xf,
	'IRSELECT' => 0x2,
	'IRCAPTURE' => 0x3,
	'IRSHIFT' => 0x4,
	'IREXIT1' => 0x5,
	'IRPAUSE' => 0x6,
	'IREXIT2' => 0x7,
	'IRUPDATE' => 0x8
);

sub OpenPort($)
{
	my $strPortName = shift;
	
	# Open serial port and configure
	$port = new Win32::SerialPort($strPortName, quiet)
			   || die "Could not open the port specified";
			   
	$port->baudrate(9600);
	$port->parity("none");
	$port->databits(8);
	$port->stopbits(1);
	$port->handshake("none");
	$port->buffers(4096, 4096); 
	$port->read_interval(100);   
	$port->read_char_time(5);  
	$port->read_const_time(100); 
	$port->write_char_time(5);
	$port->write_const_time(100);
	$port->lookclear();
	
	return $port;
}

sub SendAndReceive($$$$$)
{
	my $port = shift;
	my $SendData = shift;
	my $SendLen = shift;
	my $ReceiveData = shift;
	my $ReceiveLen = shift;
	
	$port->lookclear();
	
	$BytesWritten = $port->write($SendData);
	if($BytesWritten !=  $SendLen)
	{
		return 0;
	}

	($count, $$ReceiveData) = $port->read($ReceiveLen);
	if($count != $ReceiveLen)
	{
		return 0;		
	}
	
	if($$ReceiveData =~ /\?/)
	{
		print "Chipmunk returned error at line number $LineNumber\n";
		$port->close();
		die;
	}

	return $count ;
}

sub EchoOn()
{
	SendAndReceive($port, "echo on\r", 9, NULL, NULL);
}

sub EchoOff()
{
	SendAndReceive($port, "echo off\r", 10, NULL, NULL);
	#Dummy read to clear input buffer. LookClear seems to be not working
	$port->read(0xff);
}

#Get firmware version
sub GetVersion($)
{
	my $port = shift;
	my $tmpString;
	
	if(SendAndReceive($port, "ver\r",4, \$tmpString, 8))
	{
		return $tmpString;
	}
	
	return NULL;
}

#Set enddr
sub Enddr($$)
{
	my $port = shift;
	my $state = shift;
	my $tmpString;
	
	SendAndReceive($port, "enddr ".sprintf("%x", $state)."\r",8, \$tmpString, 8);
}

#Set enddir
sub Endir($$)
{
	my $port = shift;
	my $state = shift;
	my $tmpString;
	
	SendAndReceive($port, "endir ".sprintf("%x", $state)."\r",8, \$tmpString, 8);
}

#Put the JTAG TAP to reset state
sub Reset($)
{
	my $port = shift;
	my $tmpString;
	
	SendAndReceive($port, "reset\r",6, \$tmpString, 0);
}

#Advance TAP state machine
sub TapAdvance($$)
{
	my $port = shift;
	my $tms = shift;
	my $tmpString;
	
	SendAndReceive($port, "a ".sprintf("%x", $tms)."\r",4, \$tmpString, 2);
}

#Go to a specific TAP state
sub GoToState($$)
{
	my $port = shift;
	my $state = shift;
	my $tmpString;
	
	SendAndReceive($port, "g ".sprintf("%x", $state)."\r",4, \$tmpString, 2);
}

sub GetState($)
{
	my $port = shift;
	my $tmpString;
	
	if(SendAndReceive($port, "q\r",2 , \$tmpString, 1) != 0)
	{
		return $tmpString;
	}
	return NULL;
}

sub SelectIR($)
{
	my $port = shift;
	my $tmpString;
	my $state;
	
	SendAndReceive($port, "i\r",2 , \$tmpString, 1);
	
	$state = GetState($port);
	if($state ne "4")
	{
		GoToState($port, 0);
		SendAndReceive($port, "i\r",2 , \$tmpString, 1);
	}
	
	$state = GetState($port);
	return $state;
}

sub SelectDR($)
{
	my $port = shift;
	my $tmpString;
	my $state;
	
	SendAndReceive($port, "d\r",2 , \$tmpString, 1);
	
	$state = GetState($port);
	if($state ne "B")
	{
		GoToState($port, 0);
		SendAndReceive($port, "d\r",2 , \$tmpString, 1);
	}
	
	$state = GetState($port);
	return $state;
}

#Scan the selected register
sub Scan($$$$)
{
	my $port = shift;
	my $Tdi = shift;
	my $TdiLen = shift;
	my $ExitState = shift;
	
	if($TdiLen > 32)
	{
		return NULL;
	}
	
	if($ExitState == 0)
	{
		if(SendAndReceive($port, "s ". substr($Tdi, 0, ceil($TdiLen/4)) ." ". sprintf("%02x", $TdiLen)."\r", ceil($TdiLen/4)+6, \$tmpString, (ceil($TdiLen/4))))
		{
			return $tmpString;
		}
		else
		{
			return NULL;
		}
	}
	else
	{
		if(SendAndReceive($port, "x ". substr($Tdi, 0, ceil($TdiLen/4)) ." ". sprintf("%02x", $TdiLen)."\r", ceil($TdiLen/4)+6, \$tmpString, (ceil($TdiLen/4))))
		{
			return $tmpString;
		}
		else
		{
			return NULL;
		}
	}
}

#Runtest
sub Runtest($$)
{
	my $port = shift;
	my $cycles = shift;
	my $tmpString;
	
	SendAndReceive($port, "r ".sprintf("%x", $cycles)."\r",4 , \$tmpString, 0);
	
	#Wait a ltille bit before issuing next command
	usleep($cycles/2);
}

#Load SVF file and process
sub RunSVF($$)
{
	my $port = shift;
	my $FileName = shift;
	
	print "Processing SVF, please wait\n";
	
	open(SVF, "<$FileName");
	
	while(!eof(SVF))
	{
		my $line = <SVF>;
		$LineNumber++;
		
		print "Processing line $LineNumber\r";
		
		#Check and strip any comments
		if($line =~ /\/\//i)
		{
			$line = substr($line, 0, @- - 1);
		}
		
		#strip extra white spaces
		$line =~ s/[\h\v]+/ /g;
		
		if($line =~ /TRST/i)
		{
			#Ignore
		}
		elsif($line =~ /ENDIR/i)
		{
			if($line !~ /;/)
			{
				print "Error at line no. $LineNumber";
				return;
			}
			
			EndirHandler($port, $line);
		}
		elsif($line =~ /ENDDR/i)
		{
			if($line !~ /;/)
			{
				print "Error at line no. $LineNumber";
				return;
			}
			
			EnddrHandler($port, $line);
		}
		elsif($line =~ /STATE/i)
		{
			if($line !~ /;/)
			{
				print "Error at line no. $LineNumber";
				return;
			}
			
			StateHandler($port, $line);
		}
		elsif($line =~ /RUNTEST/i)
		{
			if($line !~ /;/)
			{
				print "Error at line no. $LineNumber, missing semicolon";
				return;
			}
			
			RuntestHandler($port, $line);
		}
		elsif($line =~ /SIR/i)
		{
			SirHandler($port, $line);
		}
		elsif($line =~ /SDR/i)
		{
			#Sometimes SDR TDI data can be very long spanning multiple lines
			my $end = 0;
			while(!$end)
			{
				if($line =~ /\)/)
				{
					SdrHandler($port, $line, 1);
					$end = 1;
				}
				else
				{
					SdrHandler($port, $line, 0);
					$line = <SVF>;
					$LineNumber++;
				}
			}	
		}
	}
	
	close SVF;
	print "\nDone\n";
	return;
}

sub SirHandler($$)
{
	my $port = shift;
	my $line = shift;

	SelectIR($port);
	
	$line =~ /SIR *([0-9]*) *TDI *\(([0-9a-fA-F]+)\)/i;
	Scan($port, $2, $1, 1);
}

sub SdrHandler($$$)
{
	my $port = shift;
	my $line = shift;
	my $end = shift;
	
	my $LineLength = 0;
	my $i = 0;
	
	if($line =~ /SDR +([0-9]+)/i)
	{
		$TdiLength = $1;
		
		$line =~ /TDI +\((.+)/i;		
		$line = $1;
	}

	if($end)
	{
		$line =~ /([0-9a-fA-F]*)\)/i;
		$line = $1;
	}

	$line =~ s/\s+$//;
	
	SelectDR($port);
	
	$LineLength = length($line) * 4;
	
	if($LineLength > $TdiLength)
	{
		$line = substr($line, floor(($LineLength - $TdiLength)/4), $LineLength/4);		
		$LineLength = $TdiLength;
	}
	
	my $AdjustedLineLength = ceil($LineLength/4);
	
	while($LineLength)
	{
		if($LineLength >= 32)
		{
			$i = $i + 8;
			Scan($port, substr($line, -$i, 8) , 32, 0);
			$LineLength = $LineLength - 32;
			$TdiLength = $TdiLength - 32;
		}
		else
		{
			Scan($port, substr($line,-($AdjustedLineLength),$AdjustedLineLength - $i) , $LineLength, $end);
			$LineLength = 0;
		}
	}

}

sub RuntestHandler($$)
{
	my $port = shift;
	my $line = shift;
	$line =~ /\s+(.*)\s*;/i;
	
	if($line !~ /TCK/i)
	{
		print "Error at line no. $LineNumber, only TCK is supported with RUNTEST";
	}
	
	$line =~ /\s+(.*)\s*;/i;
	
	Runtest($port , $1);
}

sub EndirHandler($$)
{
	my $port = shift;
	my $line = shift;
	$line =~ /\s+(.*)\s*;/i;
	Endir($port , $JTAG_STATES{$1});
}

sub EnddrHandler($$)
{
	my $port = shift;
	my $line = shift;
	$line =~ /\s+(.*)\s*;/i;
	Enddr($port , $JTAG_STATES{$1});
}

sub StateHandler($$)
{
	my $port = shift;
	my $line = shift;
	$line =~ /\s+(.*)\s*;/i;
	GoToState($port , $JTAG_STATES{$1});
}


##################################################################################

$serport = OpenPort($portName);

EchoOff();
RunSVF($serport, $FileName);

$serport->close();