'''
    PlatformIO ( WizIO 2023 Georgi Angelov )
        TEMPLATE: main.py ( simple blink )
'''
from machine import Pin, Timer

print( 'Hello World' )

led = Pin( 25, Pin.OUT )

t = Timer()

def t_callback( timer ):
    led.toggle()
    print('blink')

t.init( freq = 1, mode = Timer.PERIODIC, callback = t_callback )