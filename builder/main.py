'''
Copyright 2023 WizIO ( Georgi Angelov )
'''

import time
from os.path import join
from SCons.Script import AlwaysBuild, DefaultEnvironment, Default
from frameworks.pico_pio_asm import dev_pio_asm
from frameworks.wiz import ERROR

env = DefaultEnvironment()
env.Replace( 
    BUILD_DIR = env.subst('$BUILD_DIR'),
    ARFLAGS = ['rc'],        
    AR = 'arm-none-eabi-ar',
    AS = 'arm-none-eabi-as',
    CC = 'arm-none-eabi-gcc',
    GDB = 'arm-none-eabi-gdb',
    CXX = 'arm-none-eabi-g++',
    OBJCOPY = 'arm-none-eabi-objcopy',
    RANLIB = 'arm-none-eabi-ranlib',
    #SIZETOOL = 'arm-none-eabi-size',
) 

###############################################################################

def pico_reset_boot(*args, **kwargs):
    from frameworks.uf2conv import dev_reset_to_boot
    if 'Pico-SDK' in env['PIOFRAMEWORK'][0]:
        dev_reset_to_boot(env)

env.AddCustomTarget(
    "pico_reset_boot", None, pico_reset_boot,
    title="Pico Reset to Boot",
    description="depends from pico-stdio-usb",
)

prg = None

# PLATFORMIO  #################################################################
if 'Pico-SDK-WizIO' in env['PIOFRAMEWORK'] or 'Pico-SDK-Arduino' in env['PIOFRAMEWORK']: 
    dev_pio_asm(env)
    elf = env.BuildProgram()
    bin = env.ELF2BIN( join('$BUILD_DIR', '${PROGNAME}'), elf )
    uf2 = env.BIN2UF2( join('$BUILD_DIR', '${PROGNAME}'), bin )
    prg = env.Alias( 'buildprog', uf2)

# CMAKE #######################################################################
elif 'Pico-SDK-CMAKE' in env['PIOFRAMEWORK']:
    env.ProcessProgramDeps()
    prg = env.ACT( join('$BUILD_DIR', '${PROGNAME}'), prg )

# PYTHON ######################################################################
elif 'Pico-MicroPython' in env['PIOFRAMEWORK'] or 'RPI-Python' in env['PIOFRAMEWORK']: 
    env.BuildFrameworks( env['PIOFRAMEWORK'] )
    prg = env.ACT( join('$BUILD_DIR', '${PROGNAME}'), prg )
    env['PROJECT_INCLUDE_DIR'] = env['CPPDEFINES'] = None  

# RPI  ########################################################################
elif 'RPI-CPP' in env['PIOFRAMEWORK']: 
    elf = env.BuildProgram()
    prg = env.Alias( 'buildprog', elf )

elif 'RPI-Arduino' in env['PIOFRAMEWORK']: 
    # TODO
    pass

else: ERROR('[MAIN] Wrong platform: %s' % env['PIOFRAMEWORK'][0])

AlwaysBuild( prg )

# DEBUG ####################################################################### TODO
debug_tool = env.GetProjectOption('debug_tool')
if None == debug_tool:
    Default( prg )
else:   
    Default( prg )

# UPLOAD ######################################################################
upload = env.Alias('upload', prg, env.VerboseAction('$UPLOADCMD', ' - Uploading'), ) 
AlwaysBuild( upload )

#print(env.Dump())
