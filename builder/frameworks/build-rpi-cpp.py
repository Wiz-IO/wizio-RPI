'''
Copyright 2023 WizIO ( Georgi Angelov )
'''

import subprocess
from os import listdir, startfile
from os.path import join
from SCons.Script import DefaultEnvironment
from platform import system

###############################################################################

def init_Template(env):
    dir = join( env.subst('$PROJECT_DIR'), 'src' )
    if not listdir( dir ):
        open(join(dir, 'main.c'), 'w').write('''
#include <stdio.h>

int main(void) {
    printf("Hello World ( PlatformIO 2022 Georgi Angelov )\n");
    for(int i = 0; i < 5; i++)
        printf("\t%d\n", i);
    printf("\nClick <Enter> for end\n");
    getchar();
    return 0;
}
''' )

def run_application(target, source, env):
    s = system().lower() == 'windows'
    if s:
        startfile( env.subst(join('$BUILD_DIR', "program.exe")) )
    elif s == 'linux': # TODO
        subprocess.call([ 'gnome-terminal', '-x', env.subst(join('$BUILD_DIR', "program")) ])
    print(' * Upload DONE')

env = DefaultEnvironment()

env.Replace(
    BUILD_DIR = env.subst('$BUILD_DIR'),
    AR='ar',
    AS='as',
    CC='gcc',
    GDB='gdb',
    CXX='g++',
    OBJCOPY='objcopy',
    RANLIB='ranlib',
    ARFLAGS=['rc'],
    PROGSUFFIX = '.exe' if system().lower() == 'windows' else '',
)

env.Append(
    CPPPATH = [
        join('$PROJECT_DIR', 'src'),
        join('$PROJECT_DIR', 'lib'),
        join('$PROJECT_DIR', 'include')
    ],
    CFLAGS = [],
    CCFLAGS = [],
    CXXFLAGS = [],
    LINKFLAGS = [],
    LIBSOURCE_DIRS = [
        join('$PROJECT_DIR', 'lib'), # TODO check
    ],
    LIBS = [],
    UPLOADCMD = run_application
)

init_Template(env)

###############################################################################
