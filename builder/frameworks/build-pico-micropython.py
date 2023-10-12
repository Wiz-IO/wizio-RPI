'''
Copyright 2023 WizIO ( Georgi Angelov )
'''

import sys
from SCons.Script import DefaultEnvironment
from platformio import proc
from os import listdir, remove
from os.path import join, exists
from shutil import copyfile
from common import INFO, ERROR, MKDIR, dev_init_no_compiler, dev_remove_no_folders

try:
    from rshell.main import num_devices, autoscan, connect, Shell
except:
    ERROR('RShell not found')

def enable_Lint():
    stubs = env.GetProjectOption('custom_stubs',  'micropython-v1_19_1-rp2')
    path = join( env.subst('$PLATFORM_DIR'), 'modules', 'microPython', stubs ).replace('\\','/')
    fn = join( env.subst('$PROJECT_DIR'), 'common', 'pylintrc.txt') 
    if not exists(fn):
        f = open(fn, 'w')
        f.write('[MASTER]\n')
        f.write('init-hook=')
        f.write("'")
        f.write('import sys;sys.path[1:1] = ["%s"]' % path)
        f.write("'\n")
        f.write('disable = missing-docstring, line-too-long, trailing-newlines, broad-except, logging-format-interpolation, invalid-name,\n')
        f.write('    no-method-argument, assignment-from-no-return, too-many-function-args, unexpected-keyword-arg, missing-final-newline,\n')
        f.write('    unused-argument, \n')
        f.write('\n')
        f.close()
    fn = join( env.subst('$PROJECT_DIR'), '.vscode', 'settings.json')
    if not exists(fn):
        p = p.replace('/', '\\\\')
        f = open(fn, 'w')
        f.write('{\n')
        f.write('    "python.analysis.extraPaths": [\n        "%s",\n    ],\n' % path)
        f.write('    "python.linting.enabled": true,\n')
        f.write('    "python.linting.pylintEnabled": true,\n')
        f.write('    "python.linting.pylintArgs": [ "--rcfile", "${workspaceFolder}/common/pylintrc.txt" ],\n') 
        f.write('    "python.linting.ignorePatterns": [ "**/.platformio/**/*.py", ],\n')
        f.write('    \n')
        f.write('}\n')
        f.close()

def remove_Lint():
    fn = join( env.subst('$PROJECT_DIR'), '.vscode', 'settings.json')
    if exists(fn): remove(fn)

def init_Template(env):
    dir = join( env.subst('$PROJECT_DIR'), 'src' )
    if not listdir(dir): # CREATE MODE
        dev_remove_no_folders(env)
        copyfile(join(env.platform_dir, 'templates', 'microPython', 'main.py'), 
                 join(dir, 'main.py') )
        MKDIR( join( env.subst('$PROJECT_DIR'), 'common' ) )       
    if 'enable' == env.GetProjectOption('custom_lint',  None):
        enable_Lint()
    else:
        remove_Lint()
    fn = join( env.subst('$PROJECT_DIR'), '.vscode', 'c_cpp_properties.json' )
    if exists(fn): 
        remove(fn) # this file should not       

def action_upload_py(target, source, env):
    if not exists(env.subst(join('$PROJECT_DIR', 'src', 'main.py'))):
        ERROR('src/main.py not found')      
    port = env.get('UPLOAD_PORT')
    if None == port:
        INFO('Port: Autoscan')
        autoscan()
    else:
        INFO('Port: %s' % port)
        connect(port)
    num = num_devices()
    if num == 0:
        ERROR('microPython board not found')
    elif num == 1:
        s = Shell()
        s.cmdloop('rm /pyboard/*.py')
        for file in listdir( env.subst( join( '$PROJECT_DIR', 'src' ) ) ):
            if file.endswith('.py'):
                s.cmdloop('cp src/%s /pyboard' % file)
        s.cmdloop('exit')
        print(' * Upload DONE')
    else:
        ERROR('Too many microPython boards. Add to project ini: upload_port = port name')

def action_lint(target, source, env):
    INFO('BEGIN')
    if not exists(env.subst(join('$PROJECT_DIR', 'src', 'main.py'))):
        ERROR('src/main.py not found')
    if 'enable' == env.GetProjectOption('custom_lint',  None):
        print('   ► Lint code')
        src = env.subst(join('$PROJECT_DIR', 'src'))
        args = [ 'pylint', '--rcfile=../common/pylintrc.txt', 'main.py' ]
        proc.exec_command( args, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin, cwd=src )
    else:
        INFO('Lint code: OFF')
    INFO('END')

###############################################################################

INFO('Pico microPython UF2 files: https://micropython.org/download/rp2-pico/ ')
env = DefaultEnvironment()
dev_init_no_compiler(env, action_lint, action_upload_py)
init_Template(env)

###############################################################################
