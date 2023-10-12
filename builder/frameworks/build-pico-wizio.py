'''
Copyright 2023 WizIO ( Georgi Angelov )
'''

from os import listdir
from os.path import join
from shutil import copyfile
from SCons.Script import DefaultEnvironment
from common import dev_init_compiler, dev_init_variables
from install import dev_install
from wiz import MKDIR, MODE_WIZIO

###############################################################################

def init_Template(env):
    dir = join( env.subst('$PROJECT_DIR'), 'src' )
    if not listdir( dir ):
        copyfile( join(env.platform_dir, 'templates', env['PIOFRAMEWORK'][0], 'main.c'), join(dir, 'main.c') )

        dir = join( env.subst('$PROJECT_DIR'), 'common' )
        MKDIR(dir)
        open( join(dir, 'README'), 'w').write('''This directory is intended for project specific ( private ) files. ( scripts, linker, boot ... etc )''' )     
        copyfile( join(env.platform_dir, 'templates', env['PIOFRAMEWORK'][0], 'SConscript'),        join(dir, 'SConscript') )
        copyfile( join(env.platform_dir, 'templates', env['PIOFRAMEWORK'][0], 'wrap_math.txt'),     join(dir, 'wrap_math.txt') )
        copyfile( join(env.platform_dir, 'templates', env['PIOFRAMEWORK'][0], 'wrap_mem.txt'),      join(dir, 'wrap_mem.txt') )
        copyfile( join(env.platform_dir, 'templates', env['PIOFRAMEWORK'][0], 'wrap_print.txt'),    join(dir, 'wrap_print.txt') )

        dir = join( env.subst('$PROJECT_DIR'), 'include', 'pico' ) 
        MKDIR(dir)  
        open( join(dir,'config_autogen.h'), 'w').write('''
#include "boards/pico.h" // select board
#include "cmsis/rename_exceptions.h"        
''')   
    else:
        dev_install(env, None, MODE_WIZIO)   

###############################################################################        

env = DefaultEnvironment()
dev_init_compiler(env)
init_Template(env)
dev_init_variables(env)
env.SConscript( '$PROJECT_DIR/common/SConscript', exports='env' )

###############################################################################
