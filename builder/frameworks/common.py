'''
Copyright 2023 WizIO ( Georgi Angelov )
'''

import os
from os.path import join, dirname, basename, exists
from frameworks.uf2conv import dev_uploader, dev_bin2uf
from frameworks.scommon import SMake
from frameworks.make_boot import dev_builder_boot
from SCons.Script import Builder, COMMAND_LINE_TARGETS

from wiz import INFO,LOG,ERROR,FRAMEWORK_NAME,RMDIR

###############################################################################

def NO_ACTION(target, source, env): pass

def is_integration():
    LOG(COMMAND_LINE_TARGETS)
    return "__idedata" in COMMAND_LINE_TARGETS or "idedata" in COMMAND_LINE_TARGETS

###############################################################################

def dev_get_value(env, name, default):
    return env.GetProjectOption('custom_%s' % name, # ini user config  
           env.BoardConfig().get('build.%s' % name, default) ) # default from board

def dev_show_banner(env):
    return
    if env.SHOW_BANNER:
        print('\033[1;37;41m                               ')
        print('\033[1;37;41m   PICO-SDK is out of date     ')
        print('\033[1;37;41m      Please update...         ')
        print('\033[1;37;41m                               ')

def dev_ini_add(env, txt):
    f = open( join( env.subst('$PROJECT_DIR'), 'platformio.ini' ), 'a+' )
    f.write(txt) 
    f.close()

def dev_remove_no_folders(env):
    RMDIR( join( env.subst('$PROJECT_DIR'), 'lib' ) )  
    RMDIR( join( env.subst('$PROJECT_DIR'), 'include' ) )  
    RMDIR( join( env.subst('$PROJECT_DIR'), 'test' ) )   

def dev_init_common(env):
    env['PLATFORM_DIR' ] = env.platform_dir  = env.PioPlatform().get_dir()
    env['FRAMEWORK_DIR'] = env.framework_dir = env.PioPlatform().get_package_dir( FRAMEWORK_NAME )
    env['SDK_DIR'      ] = env.SDK_DIR       = join(env.framework_dir, 'pico-sdk')
    env['PIO_DIR'      ] = env.PIO_DIR       = join(env.framework_dir, 'platformio')    

def dev_init_no_compiler(env, action, uploader):
    LOG()
    dev_init_common(env)
    env.Replace( 
        SIZETOOL = '',
        PROGSUFFIX = '',
        PIOBUILDFILES = [], 
        UPLOADCMD = uploader,    
        BUILDERS = dict( ACT = Builder( action = env.VerboseAction( action, None ), suffix = '.none' ) ), 
    ) 

def dev_init_compiler(env, application_name = 'APPLICATION'):
    LOG()
    dev_init_common(env)
          
    env.cortex = ['-march=armv6-m', '-mcpu=cortex-m0plus', '-mthumb'] 

    env.Replace( 
        SIZETOOL = 'arm-none-eabi-size',
        SIZEPROGREGEXP = r"^(?:\.boot2|\.text|\.data|\.rodata|\.text.align|\.ARM.exidx)\s+(\d+).*",
        SIZEDATAREGEXP = r'^(?:\.data|\.bss|\.ram_vector_table)\s+(\d+).*',
        SIZECHECKCMD = '$SIZETOOL -A -d $SOURCES',
        #SIZEPRINTCMD = '$SIZETOOL --mcu=arm -C -d $SOURCES', # TODO check?
        PROGSUFFIX = '.elf',
        PROGNAME = env.GetProjectOption('custom_name', application_name) # INIDOC 
    )   

    env['SDK_LINKER_DIR' ] = env.SDK_LINKER_DIR = join(env.SDK_DIR, 'src', 'rp2_common', 'pico_standard_link')
    env['SDK_BOOT_DIR'   ] = env.SDK_BOOT_DIR   = join(env.SDK_DIR, 'src', 'rp2_common', 'boot_stage2')
    env['PIO_BOOT_DIR'   ] = env.PIO_BOOT_DIR   = join(env.PIO_DIR, 'boot')

    env.optimization = env.GetProjectOption('custom_optimization', '-Os') # INIDOC
    INFO('OPTIMIZATION  : %s' % env.optimization)        
    
    env.Append( 
        ASFLAGS=[ env.cortex, '-x', 'assembler-with-cpp' ],
        CPPDEFINES = [
            'NDEBUG',
            'PICO_ON_DEVICE=1',
        ],
        CPPPATH = [
            join("$PROJECT_DIR", "src"),
            join("$PROJECT_DIR", "lib"),
            join("$PROJECT_DIR", "include"),
            join(env.PIO_DIR, 'include'),
        ],
        #CFLAGS = [],
        CCFLAGS = [ env.cortex, env.optimization,
            "-fdata-sections",
            "-ffunction-sections",
            "-Wall",
            "-Wextra",
            "-Wfatal-errors",
            "-Wno-unused-parameter",
            "-Wno-unused-function",
            "-Wno-unused-variable",
            "-Wno-unused-value",
        ],
        CXXFLAGS = [
            '-fno-rtti',
            '-fno-exceptions',
            '-fno-threadsafe-statics',
            '-fno-non-call-exceptions',
            '-fno-use-cxa-atexit',
        ],
        LIBSOURCE_DIRS = [ 
            join('$PROJECT_DIR', 'lib'), 
        ],
        LIBPATH = [ 
            join('$PROJECT_DIR', 'lib'), 
        ],
        LIBS = [
            'm', 'c', 'gcc'
        ], 
        LINKFLAGS = [ env.cortex, env.optimization,
            '--specs=nosys.specs',
            '-nostartfiles',
            '-Wl,-Map=%s.map' % env.subst(join('$BUILD_DIR','$PROGNAME')),
            '-Wl,--gc-sections',
            '--entry=_entry_point',
        ],       
        BUILDERS = dict(
            ELF2BIN = Builder(
                action = env.VerboseAction(' '.join([ '$OBJCOPY', '-O',  'binary', '$SOURCES', '$TARGET', ]), 'Building $TARGET'), 
                suffix = '.bin'
            ),
            BIN2UF2 = Builder( 
                action = env.VerboseAction(dev_bin2uf, ' - Creating UF2'),
                suffix = '.none'
            )
        ),
        UPLOADCMD = dev_uploader        
    )

###############################################################################

def init_boot(env): # @ WizIO
    LOG()

    env.boot_src       = None
    env.boot_name      = env.GetProjectOption('custom_boot', 'boot2_w25q080.S') # INIDOC
    env.boot_file_path = env.subst( env.boot_name )

    fn, fe = os.path.splitext( basename( env.boot_file_path ) ) 
    if fe != '.S' :
        ERROR('BOOT IS NOT ASSEMBLER FILE ( .S ): %s' % basename( env.boot_file_path ) ) 

    if os.path.exists( env.boot_file_path ): # user select
        if False == os.path.isabs( env.boot_file_path ):
            env.boot_file_path = join( env.subst('$PROJECT_DIR'), env.boot_file_path)
        txt = open(env.boot_file_path, 'r').read()
        if txt.startswith('// Padded and checksummed'):
            env.boot_src = None
        elif '#include "hardware' in txt:
            env.boot_src = env.boot_file_path 
        else:
            ERROR('BOOT FILE IS UNKNOW: %s' % env.boot_file_path)
        INFO('BOOT          : %s ( user config )' % env.boot_name) 
    else:
        if os.path.exists( join(env.PIO_BOOT_DIR, env.boot_name) ): 
            INFO('BOOT          : %s ( pre compiled )' % env.boot_name)
            env.boot_file_path = join(env.PIO_BOOT_DIR, env.boot_name)
        elif os.path.exists( join( env.SDK_BOOT_DIR, env.boot_name ) ):
            INFO('BOOT          : %s ( sdk source code )' % env.boot_name)
            env.boot_src = join( env.SDK_BOOT_DIR, env.boot_name )
        else:
            ERROR('BOOT NAME IS UNKNOW: %s' % env.boot_name)    

    if env.boot_src != None:

        env.sProgName, ext = os.path.splitext( env.boot_name )
        res = SMake(env, dev_builder_boot, join( dirname(__file__), 'build-boot.py' ))
        if 0 != res:
            ERROR('Make Boot: %s' % res)
        env.BuildSources( 
            join('$BUILD_DIR', 'boot'),
            join('$SMAKE_BUILD_DIR'),
        )         
    else:
        env.BuildSources(
            join('$BUILD_DIR', 'boot'),
            dirname( env.boot_file_path ),
            '-<*> +<%s>' % basename( env.boot_file_path )
        ) 

def init_binary(env, txt = 'board'): # @ WizIO
    LOG() 

    env.binary = dev_get_value(env, 'binary', 'default') # INIDOC
    INFO('BINARY TYPE   : %s' % env.binary)

    env.address = '0x10000000'
    env.linker = dev_get_value(env, 'linker', join(env.SDK_LINKER_DIR, 'memmap_default.ld')) # INIDOC
    env.linker = env.subst(env.linker)

    if 'copy_to_ram' == env.binary:
        env.linker  = join(env.SDK_LINKER_DIR, 'memmap_copy_to_ram.ld')
        env.Append( CPPDEFINES = ['PICO_COPY_TO_RAM'] )    

    elif 'no_flash' == env.binary:
        env.address = '0x20000000'
        env.linker  = join(env.SDK_LINKER_DIR, 'memmap_no_flash.ld')
        env.Append( CPPDEFINES = ['PICO_NO_FLASH'] )  

    elif 'blocked_ram' == env.binary[0]: # TODO: no info
        ERROR('TODO: blocked_ram - how?')  

    env['LDSCRIPT_PATH'] = env.linker if 'pico_standard_link' in env.linker else env.linker
    INFO('LINKER        : %s' % basename(env['LDSCRIPT_PATH']))

    env.address = dev_get_value(env, 'address', env.address) # INIDOC   

def dev_init_variables(env): # @ WizIO
    LOG()

    if is_integration(): 
        return    

    env.heap = dev_get_value(env, 'heap', '2048') # INIDOC
    INFO('HEAP          : %s' % env.heap )

    env.stack = dev_get_value(env, 'stack', '2048') # INIDOC
    INFO('STACK         : %s' % env.stack)

    init_binary(env)

    init_boot(env)

###############################################################################

def dev_build_cyw43_firmware(env, dst_path, TRIGGER, name = '43439A0-7.95.49.00.combined'):
    LOG()

    NAME = name.replace('.combined', '').replace('-', '_').replace('.', '_')
    FIRMWARE_OBJ = join(dst_path, 'CYW43_' + NAME + '.o')

    if exists(FIRMWARE_OBJ): 
        return NAME

    FIRMWARE_BIN = join( env.SDK_DIR, "lib", "cyw43-driver", "firmware", name )
    
    old_name = FIRMWARE_BIN
    old_name = '_binary_' + old_name.replace('\\\\', '_').replace('\\', '_').replace('/', '_').replace('.', '_').replace(':', '_').replace('-', '_')
    CMD = [ "$OBJCOPY", "-I", "binary", "-O", "elf32-littlearm", "-B", "arm", "--readonly-text",
            "--rename-section", ".data=.big_const,contents,alloc,load,readonly,data",
            "--redefine-sym", old_name + "_start=fw_%s_start" % NAME,
            "--redefine-sym", old_name + "_end=fw_%s_end"     % NAME,
            "--redefine-sym", old_name + "_size=fw_%s_size"   % NAME,
            FIRMWARE_BIN, # SOURCE BIN
            FIRMWARE_OBJ  # TARGET OBJ
    ]
    env.AddPreAction( 
        TRIGGER,
        env.VerboseAction(" ".join( CMD ), "Compiling Firmware: %s" % 'CYW43_' + NAME, ) 
    )       

    env.Append( LIBS = [ env.File( FIRMWARE_OBJ ) ] )
    return NAME

###############################################################################
