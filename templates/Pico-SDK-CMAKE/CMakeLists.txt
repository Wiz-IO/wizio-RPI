cmake_minimum_required(VERSION 3.12)

include(pico_sdk_import.cmake)

project(blink)

pico_sdk_init()

add_executable(blink
    main.c
)

pico_add_extra_outputs(blink)

target_link_libraries(blink pico_stdlib)