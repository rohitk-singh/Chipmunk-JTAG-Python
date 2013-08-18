Chipmunk-JTAG-Python
====================

Python port of Chipmunk JTAG's original API written in perl

Files:

-- README.md
-- XC9572XL.pl
-- XC9572XL.py
-- Sample_SVFs
      -- README.md
      -- counter.svf
      -- lcd_v02.svf
      -- switches_leds.svf
  
  
# XC9572XL.pl
  Original Perl code from numato.cc
  
# XC9572XL.py
  Ported python code 
  

USAGE:

type    : "python XC9572XL.py COMx file.svf"
example : "python XC9572XL.pu COM45 counter.svf"


DEPENDENCIES:

# PySerial -- Requires pySerial module for python. Can be download from pyserial.sourceforge.net


OPERATING SYSTEMS:

Has been tested only on windows till now. But, the code and required modules are OS independent.
Hence, Linux testing is required to confirm its working.


WARNING: The python code will output LOTS of messages (required for debugging purpose) during running. 
         Unless there is an error, you can safely ignore all the messages. 
         Those message will be removed soon. Sorry for annoyance. 
         EXPERIMENTAL RELEASE. Not guaranteed for 
         production and/or critical environment.
