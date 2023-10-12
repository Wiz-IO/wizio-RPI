'''
Copyright 2023 WizIO ( Georgi Angelov )
'''

import subprocess
from os import listdir, startfile
from os.path import join
from SCons.Script import DefaultEnvironment
from platform import system
from common import dev_init_no_compiler

###############################################################################

def init_Template(env):
    dir = join( env.subst('$PROJECT_DIR'), 'src' )
    if not listdir( dir ):
        open(join(dir, 'main.py'), 'w').write('''
import time

print('Hello World ( PlatformIO 2023 Georgi Angelov )')
for i in range(5):
    print('\t', i)
    time.sleep(1)
''' )

def action_run_py(target, source, env):
    s = system().lower() == 'windows'
    if s:
        startfile( env.subst(join('$PROJECT_DIR', 'src', 'main.py')) )
    elif s == 'linux':
        subprocess.call([ 'gnome-terminal', '-x', env.subst(join('$PYTHONEXE, $PROJECT_DIR', 'main.py')) ]) # TODO
    print(' * Upload DONE')

def action_py(target, source, env):
    # TODO: Lint?
    pass

###############################################################################

env = DefaultEnvironment()
dev_init_no_compiler(env, action_py, action_run_py)
init_Template(env)