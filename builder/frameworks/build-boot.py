'''
Copyright 2023 WizIO ( Georgi Angelov )
'''

import os
from os.path import join, basename
from shutil import copyfile
from scommon import SCreate

###############################################################################

def generate_bin(source, target, env, for_signature):
    return "$OBJCOPY -O binary $SOURCES $TARGET"

def generate_asm(target, source, env):
    bin = source[0].rstr()
    asm = target[0].rstr()
    py = join(env['SDK_DIR'], 'src', 'rp2_common', 'boot_stage2', 'pad_checksum')
    env.Execute('python ' + py + ' -s 0xffffffff ' + bin + ' ' + asm)

    if 'boot2_' in asm: # move to 'platformio/boot'
        copyfile( asm, join( env['PIO_BOOT_DIR'], basename(asm) ) )
        print( '   Boot Stage Done ( moved )' )
    else:
        print( '   Boot Stage Done' )

###############################################################################

env = SCreate()

print( '   Compiling Boot Stage: %s' % env['PROGNAME'] )

env.Append( 
    BUILDERS =
    { 
        'ELF2BIN': env.Builder( generator = generate_bin, suffix ='.bin', src_suffix ='.elf'), 
        'BIN2ASM': env.Builder( action    = generate_asm, suffix ='.S',   src_suffix ='.bin'), 
    }
)

A = env.Program( 
    target = env.subst( join( env['BUILD_DIR'], env['PROGNAME'] ) ),
    source = env['SOURCE_CODE'] 
)

B = env.ELF2BIN(A)

C = env.BIN2ASM(B)

env.AlwaysBuild(C)

###############################################################################