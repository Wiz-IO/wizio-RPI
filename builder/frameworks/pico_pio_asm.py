###############################################################################
#
#  SPDX-FileCopyrightText:
#         Copyright (c) 2021 Scott Shawcroft for Adafruit Industries LLC
#
#         https://github.com/adafruit/Adafruit_CircuitPython_PIOASM
#
#  SPDX-License-Identifier: MIT
#
#  MOD: WizIO 2022 Georgi Angelov
#
###############################################################################

import os, array, re
from os.path import join, exists, basename
from os.path import join, basename
from wiz import ERROR, INFO

###############################################################################

splitter = re.compile(r",\s*|\s+(?:,\s*)?").split
mov_splitter = re.compile("!|~|::").split

CONDITIONS = ["", "!x", "x--", "!y", "y--", "x!=y", "pin", "!osre"]
IN_SOURCES = ["pins", "x", "y", "null", None, None, "isr", "osr"]
OUT_DESTINATIONS = ["pins", "x", "y", "null", "pindirs", "pc", "isr", "exec"]
WAIT_SOURCES = ["gpio", "pin", "irq", None]
MOV_DESTINATIONS = ["pins", "x", "y", None, "exec", "pc", "isr", "osr"]
MOV_SOURCES = ["pins", "x", "y", "null", None, "status", "isr", "osr"]
MOV_OPS = [None, "~", "::", None]
SET_DESTINATIONS = ["pins", "x", "y", None, "pindirs", None, None, None]

class PIO_ASM_COMPILER:  # pylint: disable=too-few-public-methods
    def __init__(self, text_program: str, *, build_debuginfo=False) -> None:
        """Converts pioasm text to encoded instruction bytes"""
        # pylint: disable=too-many-branches,too-many-statements,too-many-locals
        assembled = []
        program_name = None
        labels = {}
        linemap = []
        instructions = []
        sideset_count = 0
        sideset_enable = 0
        wrap = None
        wrap_target = None
        for i, line in enumerate(text_program.split("\n")):
            line = line.strip()
            if not line:
                continue
            if ";" in line:
                line = line.split(";")[0].strip()
            if line.startswith(".program"):
                if program_name:
                    raise RuntimeError(
                        PIO_ASM_ERROR("Multiple programs not supported")
                    )

                program_name = line.split()[1]
            elif line.startswith(".wrap_target"):
                wrap_target = len(instructions)
            elif line.startswith(".wrap"):
                if len(instructions) == 0:
                    raise RuntimeError(
                        PIO_ASM_ERROR("Cannot have .wrap as first instruction")
                    )

                wrap = len(instructions) - 1
            elif line.startswith(".side_set"):
                sideset_count = int(line.split()[1], 0)
                sideset_enable = "opt" in line
            elif line.endswith(":"):
                label = line[:-1]
                if label in labels:
                    raise SyntaxError(
                        PIO_ASM_ERROR( f"Duplicate label {repr(label)}")
                    )

                labels[label] = len(instructions)
            elif line:
                # Only add as an instruction if the line isn't empty
                instructions.append(line)
                linemap.append(i)

        max_delay = 2 ** (5 - sideset_count - sideset_enable) - 1
        assembled = []
        for instruction in instructions:
            # print(instruction)
            instruction = splitter(instruction.strip())
            delay = 0
            if instruction[-1].endswith("]"):  # Delay
                delay = int(instruction[-1].strip("[]"), 0)
                if delay < 0:
                    raise RuntimeError(
                        PIO_ASM_ERROR("Delay negative:", delay)
                    )

                if delay > max_delay:
                    raise RuntimeError(
                        PIO_ASM_ERROR("Delay too long:", delay)
                    )

                instruction.pop()
            if len(instruction) > 1 and instruction[-2] == "side":
                if sideset_count == 0:
                    raise RuntimeError(
                        PIO_ASM_ERROR("No side_set count set")
                    )

                sideset_value = int(instruction[-1], 0)
                if sideset_value >= 2**sideset_count:
                    raise RuntimeError(
                        PIO_ASM_ERROR("Sideset value too large")
                    )

                delay |= sideset_value << (5 - sideset_count - sideset_enable)
                delay |= sideset_enable << 4
                instruction.pop()
                instruction.pop()

            if instruction[0] == "nop":
                #                  mov delay   y op   y
                assembled.append(0b101_00000_010_00_010)
            elif instruction[0] == "jmp":
                #                instr delay cnd addr
                assembled.append(0b000_00000_000_00000)
                target = instruction[-1]
                if target[:1] in "0123456789":
                    assembled[-1] |= int(target, 0)
                elif instruction[-1] in labels:
                    assembled[-1] |= labels[target]
                else:
                    raise SyntaxError(
                        PIO_ASM_ERROR(f"Invalid jmp target {repr(target)}")
                    )

                if len(instruction) > 2:
                    try:
                        assembled[-1] |= CONDITIONS.index(instruction[1]) << 5
                    except ValueError as exc:
                        raise ValueError(
                            PIO_ASM_ERROR(f"Invalid jmp condition '{instruction[1]}'")
                        ) from exc

            elif instruction[0] == "wait":
                #                instr delay p sr index
                assembled.append(0b001_00000_0_00_00000)
                polarity = int(instruction[1], 0)
                if not 0 <= polarity <= 1:
                    raise RuntimeError(
                        PIO_ASM_ERROR("Invalid polarity")
                    )

                assembled[-1] |= polarity << 7
                assembled[-1] |= WAIT_SOURCES.index(instruction[2]) << 5
                num = int(instruction[3], 0)
                if not 0 <= num <= 31:
                    raise RuntimeError(
                        PIO_ASM_ERROR("Wait num out of range")
                    )

                assembled[-1] |= num
                if instruction[-1] == "rel":
                    assembled[-1] |= 0x10  # Set the high bit of the irq value
            elif instruction[0] == "in":
                #                instr delay src count
                assembled.append(0b010_00000_000_00000)
                assembled[-1] |= IN_SOURCES.index(instruction[1]) << 5
                count = int(instruction[-1], 0)
                if not 1 <= count <= 32:
                    raise RuntimeError(
                        PIO_ASM_ERROR("Count out of range")
                    )

                assembled[-1] |= count & 0x1F  # 32 is 00000 so we mask the top
            elif instruction[0] == "out":
                #                instr delay dst count
                assembled.append(0b011_00000_000_00000)
                assembled[-1] |= OUT_DESTINATIONS.index(instruction[1]) << 5
                count = int(instruction[-1], 0)
                if not 1 <= count <= 32:
                    raise RuntimeError(
                        PIO_ASM_ERROR("Count out of range")
                    )

                assembled[-1] |= count & 0x1F  # 32 is 00000 so we mask the top
            elif instruction[0] == "push" or instruction[0] == "pull":
                #                instr delay d i b zero
                assembled.append(0b100_00000_0_0_0_00000)
                if instruction[0] == "pull":
                    assembled[-1] |= 0x80
                if instruction[-1] == "block" or not instruction[-1].endswith("block"):
                    assembled[-1] |= 0x20
                if len(instruction) > 1 and instruction[1] in ("ifempty", "iffull"):
                    assembled[-1] |= 0x40
            elif instruction[0] == "mov":
                #                instr delay dst op src
                assembled.append(0b101_00000_000_00_000)
                assembled[-1] |= MOV_DESTINATIONS.index(instruction[1]) << 5
                source = instruction[-1]
                source_split = mov_splitter(source)
                if len(source_split) == 1:
                    try:
                        assembled[-1] |= MOV_SOURCES.index(source)
                    except ValueError as exc:
                        raise ValueError(
                            PIO_ASM_ERROR(f"Invalid mov source '{source}'")
                        ) from exc

                else:
                    assembled[-1] |= MOV_SOURCES.index(source_split[1])
                    if source[:1] == "!":
                        assembled[-1] |= 0x08
                    elif source[:1] == "~":
                        assembled[-1] |= 0x08
                    elif source[:2] == "::":
                        assembled[-1] |= 0x10
                    else:
                        raise RuntimeError(
                            PIO_ASM_ERROR("Invalid mov operator:", source[:1])
                        )

                if len(instruction) > 3:
                    assembled[-1] |= MOV_OPS.index(instruction[-2]) << 3
            elif instruction[0] == "irq":
                #                instr delay z c w index
                assembled.append(0b110_00000_0_0_0_00000)
                if instruction[-1] == "rel":
                    assembled[-1] |= 0x10  # Set the high bit of the irq value
                    instruction.pop()
                num = int(instruction[-1], 0)
                if not 0 <= num <= 7:
                    raise RuntimeError(
                        PIO_ASM_ERROR("Interrupt index out of range")
                    )

                assembled[-1] |= num
                if len(instruction) == 3:  # after rel has been removed
                    if instruction[1] == "wait":
                        assembled[-1] |= 0x20
                    elif instruction[1] == "clear":
                        assembled[-1] |= 0x40
                    # All other values are the default of set without waiting
            elif instruction[0] == "set":
                #                instr delay dst data
                assembled.append(0b111_00000_000_00000)
                try:
                    assembled[-1] |= SET_DESTINATIONS.index(instruction[1]) << 5
                except ValueError as exc:
                    raise ValueError(
                        PIO_ASM_ERROR(f"Invalid set destination '{instruction[1]}'")
                    ) from exc

                value = int(instruction[-1], 0)
                if not 0 <= value <= 31:
                    raise RuntimeError(
                        PIO_ASM_ERROR("Set value out of range")
                    )

                assembled[-1] |= value
            else:
                raise RuntimeError(
                    PIO_ASM_ERROR("Unknown instruction<"+instruction[0]+'>  ')
                )

            assembled[-1] |= delay << 8
            # print(bin(assembled[-1]))

        self.pio_kwargs = {
            "sideset_enable": sideset_enable,
        }

        if sideset_count != 0:
            self.pio_kwargs["sideset_pin_count"] = sideset_count

        if wrap is not None:
            self.pio_kwargs["wrap"] = wrap
        if wrap_target is not None:
            self.pio_kwargs["wrap_target"] = wrap_target

        self.assembled = array.array("H", assembled)

        if build_debuginfo:
            self.debuginfo = (linemap, text_program)
        else:
            self.debuginfo = None

    def print_c_program(self, name, qualifier="const", C=True):
        """Print the program into a C program snippet"""

        txt = '''
//-------------------------------------
//  BEGIN %s 
//-------------------------------------
''' % name

        if self.debuginfo is None:
            linemap = None
            program_lines = None
        else:
            linemap = self.debuginfo[0][:]  # Use a copy since we destroy it
            program_lines = self.debuginfo[1].split("\n")

        txt += f"{qualifier} int {name}_wrap = {self.pio_kwargs.get('wrap', len(self.assembled)-1)};" +'\n'

        txt += f"{qualifier} int {name}_wrap_target = {self.pio_kwargs.get('wrap_target', 0)};" +'\n'

        sideset_pin_count = self.pio_kwargs.get("sideset_pin_count", 0)

        txt += f"{qualifier} int {name}_sideset_pin_count = {sideset_pin_count};" +'\n'

        txt += f"{qualifier} bool {name}_sideset_enable = {int(self.pio_kwargs['sideset_enable'])};" +'\n'

        txt += f"{qualifier} uint16_t {name}_program_instructions[] = " + "{\n"

        last_line = 0
        if linemap:
            for inst in self.assembled:
                next_line = linemap[0]
                del linemap[0]
                while last_line < next_line:
                    line = program_lines[last_line]
                    if line:
                        txt += f"            // {line}" +'\n'

                    last_line += 1
                line = program_lines[last_line]
                txt += f"    0x{inst:04x}, // {line}" +'\n'

                last_line += 1
            while last_line < len(program_lines):
                line = program_lines[last_line]
                if line:
                    txt += f"            // {line}" +'\n'

                last_line += 1
        else:
            for i in range(0, len(self.assembled), 8):
                txt += "    " + ", ".join("0x%04x" % i for i in self.assembled[i : i + 8])
                txt += '\n'

        txt += "};\n"

        origin = -1
        if C: txt += '''
#if !PICO_NO_HARDWARE
static const struct pio_program %s_program = {
    .instructions = %s_program_instructions,
    .length = %d,
    .origin = %d, // not supported
};

static inline pio_sm_config %s_program_get_default_config(uint offset) {
    pio_sm_config c = pio_get_default_sm_config();
    sm_config_set_wrap(&c, offset + %s_wrap_target, offset + %s_wrap);
    sm_config_set_sideset(&c, 1, false, false);
    return c;
}
#endif
''' % (name, name, len(self.assembled), origin, name, name, name)
        return txt

###############################################################################

PIO_ERROR = ''
def PIO_ASM_ERROR(s):
    global PIO_ERROR
    PIO_ERROR = s
    return s

def get_programs(s):
    prg = []; z = []; p = []; name = None
    s = s[ s.find('.program') : ].replace('\r','')
    x = s.split(' end:')
    for i in x:
        i = i.strip()
        y = i.split('\n')
        z=[]
        name = None
        for j in y:
            if j == 'public': continue
            if j.startswith('.program'):
                name = re.sub(' +', ' ', j)
                name = name.split()[1]
                continue
            j = j.replace(': ', ': \n') # label bug
            z.append(j)
        p = '\n'.join(z)
        #print(p)
        if name: prg.append([name,p])
    return prg

def compile_pio_asm_program(name, text, D=False, Q='static const'):
    Prg = PIO_ASM_COMPILER( text, build_debuginfo=D )
    return Prg.print_c_program( name, qualifier=Q )

def compile_pio_asm_file(src, dst, info=True):
    asm = None 
    if not exists(src): 
        ERROR('PIO File not found: %s' % src)      
    f = open(src,'r')
    pio_asm = f.read()
    f.close()
    INFO('Compiling PIO ASM : %s' % src)
    programs = get_programs( pio_asm )
    if [] == programs: return asm
    asm  = '''
// PIO ASM - PlatformIO ( WizIO 2023 Georgi Angelov )

#include <stdint.h>
#if !PICO_NO_HARDWARE
#include "hardware/pio.h"
#endif
'''
    try:
        for p in programs:
            asm += compile_pio_asm_program(p[0], p[1])
            #print(asm)
        if dst: 
            f = open(dst, 'w')
            f.write(asm)
            f.close()
    except:
        #print("PIO 1")
        try:
            if dst: 
                f.close()
                if exists(dst): 
                    os.remove(dst)
        except: 
            #print("PIO ERR 2")
            pass
        #DEBUG(p[1])
        ERROR('< %s > in file: %s' % (PIO_ERROR, src))
    if info: INFO('PIO ASM DONE : % s' % join('include', basename(dst)))
    return asm

###############################################################################

def dev_pio_asm(env):
    filenames = env.GetProjectOption('custom_pioasm', '0')
    if '0' == filenames: return
    for src in filenames.split():
        src_path = env.subst(src)
        dst_path = join(env.subst('$PROJECT_DIR'), 'include', basename(src) + '.h')
        if not exists(dst_path):
            compile_pio_asm_file(src_path, dst_path)
