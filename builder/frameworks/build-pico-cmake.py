'''
Copyright 2023 WizIO ( Georgi Angelov )
'''

import sys
from os import listdir, stat
from os.path import join, exists
from shutil import copyfile
from SCons.Script import DefaultEnvironment
from platformio import proc

from uf2conv import dev_upload_uf2
from install import dev_install

from common import dev_init_no_compiler, dev_show_banner
from wiz import ERROR, INFO, FRAMEWORK_NAME, MODE_CMAKE

###############################################################################

def get_cmake_program_name(env):
    def get_name(dir):
        name = '?' 
        txt = open( join(dir, 'CMakeLists.txt'), 'r').read()
        txt = txt.replace('\n','').replace('\r','').replace('\t','').strip()
        if 'add_executable(' in txt:
            i = txt.find('add_executable(')
            name = txt[ i + 15 : txt.find(' ', i) ]
            env['PROGNAME'] = name # set upload name
        return name
    return get_name( env.subst( join('$PROJECT_DIR', 'src') ) )

def init_Template(env):
    dir = join( env.subst('$PROJECT_DIR'), 'src' )
    if not listdir( dir ):
        copyfile( join(env.platform_dir, 'templates', env['PIOFRAMEWORK'][0], 'main.c'),
                  join(dir, 'main.c') )
        copyfile( join(env.platform_dir, 'templates', env['PIOFRAMEWORK'][0], 'CMakeLists.txt'),
                  join(dir, 'CMakeLists.txt') )
        copyfile( join(env.SDK_DIR, 'external',  'pico_sdk_import.cmake'),
                  join(dir, 'pico_sdk_import.cmake') )
    else: 
        dev_install(env, None, MODE_CMAKE)
    INFO('CMAKE Executable: %s' % get_cmake_program_name( env ))

def init_IntelliSense(env): # full efect after first build
    env.Append(
        CPPPATH = [
            join("$PROJECT_DIR", "src"),
            join("$PROJECT_DIR", "lib"),
            join("$PROJECT_DIR", "include"),
            join('$BUILD_DIR', 'generated', 'pico_base'), 
            join(env.PIO_DIR, 'include'),           
        ]
    )

def add_custom_arguments(cmd, key):
    N = env.GetProjectOption(key,  None)
    if N:
        N = N.split()
        for n in N: 
            cmd.append(n)

def action_cmake(target, source, env):
    INFO('CMAKE BEGIN')
    platform = env.PioPlatform()
    PICO_SDK_PATH = join(platform.get_package_dir(FRAMEWORK_NAME), 'pico-sdk')
    PROJECT_DIR = env.subst( join('$PROJECT_DIR', 'src') )
    BUILD_DIR = env.subst('$BUILD_DIR')
    cmake = platform.get_package_dir("tool-cmake")
    env['ENV']['PATH'] += ';' + join(cmake, 'bin')
    ninja = platform.get_package_dir("tool-ninja")
    env['ENV']['PATH'] += ';' + ninja
    cmd = ['cmake',
        '-DPICO_SDK_PATH=%s' % PICO_SDK_PATH,
        '-DCMAKE_PROJECT_NAME=%s' % env.subst('$PROGNAME'),
        '-DCMAKE_BUILD_TYPE=Release',
        '-DPICO_TOOLCHAIN_PATH=%s' % join( platform.get_package_dir("toolchain-gccarmnoneeabi"), 'bin'),
        '-G', 'Ninja',
        '-S', PROJECT_DIR,
        '-B', BUILD_DIR,
    ]
    add_custom_arguments(cmd, 'custom_cmake') # INIDOC
    res = proc.exec_command( cmd, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin )
    if 0 == res['returncode']:
        cmd = ['ninja']
        add_custom_arguments(cmd, 'custom_ninja') # INIDOC
        res = proc.exec_command( cmd, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin, cwd=BUILD_DIR )
    if res['returncode']: 
        ERROR('CMAKE: %s' % res)

    env.Execute("arm-none-eabi-size -B "+join("$BUILD_DIR","${PROGNAME}.elf"), None)
    bin = env.subst(join('$BUILD_DIR', '$PROGNAME')) + '.bin'
    if exists( bin ): 
        INFO('Bin Size: %d' % stat( bin ).st_size)    
    INFO('CMAKE END')

    dev_show_banner(env)

###############################################################################

env = DefaultEnvironment()
dev_init_no_compiler(env, action_cmake, dev_upload_uf2)
init_Template(env)
init_IntelliSense(env)

###############################################################################
