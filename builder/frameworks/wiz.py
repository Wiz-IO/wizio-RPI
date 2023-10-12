'''
Copyright 2023 WizIO ( Georgi Angelov )
'''

import os, sys, shutil, time, click, inspect
from os.path import exists

PLATFORM_NAME  = 'wizio-RPI'
FRAMEWORK_NAME = 'framework-RPI'

MODE_INSTALL    = 0
MODE_INTEGRATE  = 1
MODE_PYTHON     = 2
MODE_CMAKE      = 3
MODE_WIZIO      = 4
MODE_ARDUINO    = 5
MODE_RPI        = 6

def LOG(txt = ''):
    txt = '[] %s() %s' % (inspect.stack()[1][3], txt)
    #open('F:/RPI-LOG.txt', 'a+').write(txt + '\n')
    pass

def ERROR(txt = ''):
    txt = '%s() %s' % (inspect.stack()[1][3], txt)
    click.secho( '[ERROR] %s \n' % txt, fg='red') 
    time.sleep(.1)
    sys.exit(-1)

def INFO(txt): 
    click.secho( '   %s' % (txt), fg='blue') # BUG: Windows: 4 same chars

def MKDIR(dir, test=False): 
    if dir and not exists(dir): 
        os.makedirs(dir, exist_ok=True)

def RMDIR(dir, test=False):  
    if dir and exists(dir): 
        shutil.rmtree( dir, ignore_errors=True )
        timeout = 50
        while exists( dir ) and timeout > 0: 
            time.sleep(.1)  
            timeout -= 1  
        if timeout == 0: 
            ERROR('Delete folder: %s' % dir)