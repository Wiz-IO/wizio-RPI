'''
Copyright 2023 WizIO ( Georgi Angelov )
'''

import os, sys
from os.path import join, exists

from platformio import proc, fs
from platformio.platform.base import PlatformBase
from platformio.package.manager.core import get_core_package_dir
from SCons.Defaults import DefaultEnvironment
from SCons.Script import ARGUMENTS       

###############################################################################

def sCollectBuildFiles(env, variant_dir, src_dir, src_filter=None): # private
    SRC_ASM_EXT   = ['S', 'spp', 'SPP', 'sx', 's', 'asm', 'ASM']
    SRC_C_EXT     = ['c']
    SRC_CXX_EXT   = ['cc', 'cpp', 'cxx', 'c++']
    SRC_BUILD_EXT = SRC_C_EXT + SRC_CXX_EXT + SRC_ASM_EXT    
    variants      = []

    src_dir = env.subst(src_dir)
    if src_dir.endswith(os.sep):
        src_dir = src_dir[:-1]

    for item in env.MatchSourceFiles(src_dir, src_filter, SRC_BUILD_EXT):
        _rel_dir = os.path.dirname(item)
        _src_dir = os.path.join(src_dir, _rel_dir) if _rel_dir else src_dir
        _var_dir = os.path.join(variant_dir, _rel_dir) if _rel_dir else variant_dir
        if _var_dir not in variants:
            variants.append(_var_dir)
            env['VARIANT'].append([_var_dir, _src_dir]) # ADD VARIANT FOLDER
  
        env['SOURCE_CODE'].append( os.path.join( _var_dir, os.path.basename(item) ) ) # ADD SOURCE FILES @ _var_dir

###############################################################################

def SBuildSources(env, variant_dir, src_dir, src_filter=None): # @ PIO
    sCollectBuildFiles(env, variant_dir, src_dir, src_filter)

###############################################################################

def SClone(main): # @ PIO
    env = main.Clone()

    env.Replace(
        CPPPATH         = [],
        CPPDEFINES      = [],
        CXXFLAGS        = [],
        CCFLAGS         = [],
        CFLAGS          = [],
        BUILD_SCRIPT    = [],
        LINKFLAGS       = [],  
        LIBPATH         = [],
        LIBS            = [],  
        LIBSOURCE_DIRS  = [], 
        LDSCRIPT_PATH   = '', 
        PROGNAME        = env.sProgName,                                    
    ) 

    # new build dir
    main['SMAKE_BUILD_DIR'] = env['BUILD_DIR'] = env['BUILD_DIR'].replace(
        os.path.basename( os.path.normpath( main['BUILD_DIR'] ) ),
        env.sProgName
    )
  
    env['SOURCE_CODE'] = [] 

    env['VARIANT'] = [] 

    env['GCC_BIN_DIR'] = join( main.PioPlatform().get_package_dir('toolchain-gccarmnoneeabi'), 'bin')

    return env

###############################################################################

def SMake(env, BuilderFunction, SConstructFile, Silent = True, Jobs = 1): # @ PIO
    ENV = BuilderFunction(env)
    scons_dir = get_core_package_dir('tool-scons')
    args = [
        proc.get_pythonexe_path(),
        os.path.join(scons_dir, 'scons.py'), '-Q', '%s' % '-s' if Silent else ''
        '--warn=no-no-parallel-support', '--jobs', str(Jobs),        
        '--sconstruct', SConstructFile, 
    ]

    D = ENV.Dictionary()
    for k in D: # clear out the unnecessary
        if not isinstance(D[k], (str, list, tuple, dict)): continue
        if k.startswith('_'): continue 
        if k.startswith('@'): continue
        if k.startswith('SIZE'): continue
        if '<' in str( D[k] ): continue
        if len( D[k] ) == 0: continue
        if 'ENV' == k: continue               
        args.append('%s=%s ' % (k, PlatformBase.encode_scons_arg( D[k] ) )) 
         
    res = proc.exec_command( args, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin )
    return res['returncode']

###############################################################################

def SCreate(): # @ SConstructFile
    DEFAULT_ENV_OPTIONS = dict(
        tools    = [ 'ar', 'cc', 'c++', 'link', 'pioasm', ], # other?
        toolpath = [os.path.join(fs.get_source_dir(), 'builder', 'tools')],
        ENV      = os.environ,    
    )
    command_strings = dict( 
        ARCOM     = 'Archiving',
        LINKCOM   = 'Linking',
        RANLIBCOM = 'Indexing',
        ASCOM     = 'Compiling',
        ASPPCOM   = 'Compiling',
        CCCOM     = 'Compiling',
        CXXCOM    = 'Compiling',
    )
    for name, value in command_strings.items():
        DEFAULT_ENV_OPTIONS['%sSTR' % name] = '%s $TARGET' % (value)

    env = DefaultEnvironment(**DEFAULT_ENV_OPTIONS).Clone()
    env.Replace(
        **{
            key: PlatformBase.decode_scons_arg(ARGUMENTS[key])
            for key in ARGUMENTS.keys()
        }
    )

    env['ENV']['PATH'] += ';' + env['GCC_BIN_DIR'] # add gcc/bin to path

    dir = env.subst('$BUILD_DIR')
    if not exists(dir): os.mkdir(dir)
    env.SConsignFile( join('$BUILD_DIR', '.sconsign.dblite')  ) # set path for .sconsign.

    for _var_dir, _src_dir in env['VARIANT']: # set variant dirs
        env.VariantDir(_var_dir, _src_dir, 0)

    return env

###############################################################################