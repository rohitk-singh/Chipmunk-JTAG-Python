Chipmunk-JTAG-Python
====================

Sample SVFs for XC9572XL CPLD Breakout Board from numato.com

switches_leds.svf 
        -> Press switch to change the leds

counter.svf
        -> Twin Leds glow in sequence as a counter (00--01--10--11)
        
lcd_v02.svf
        -> The LCD program at http://technologyrealm.blogspot.com/2013/07/16x2-character-lcd-interfacing-with.html
           If LCD is not connected, then twin LEDs can be used to check the working; they 
           glow as a high speed counter
