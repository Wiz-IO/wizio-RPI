'''
Copyright 2023 WizIO ( Georgi Angelov )
'''

from os.path import join, dirname, basename
from frameworks.scommon import SClone, SBuildSources

def dev_builder_boot(env):
    env = SClone(env)

    cortex = ['-mcpu=cortex-m0plus', '-mthumb']

    env.Append(
        CPPPATH = [ 
            join(env.PIO_DIR, 'include'),
            join(env.PIO_DIR, 'boot', 'include'), # config_autogen.h
        ],        
        #ASFLAGS   = [ cortex, '-x', 'assembler-with-cpp' ],
        CCFLAGS   = [ cortex ],
        LINKFLAGS = [ cortex, 
            '-Os', 
            '-nostartfiles', 
            '-nostdlib', 
            '-Wall', 
            '-Wfatal-errors',
            '--entry=_stage2_boot',
        ],
        LDSCRIPT_PATH = join(env.SDK_DIR, 'src', 'boot_stage2', 'boot_stage2.ld'), 
    )

    SBuildSources( env, 
        join('$BUILD_DIR', 'obj'), 
        dirname( env.boot_src ),
        '-<*> +<%s>' % basename( env.boot_src )
    )

    return env
