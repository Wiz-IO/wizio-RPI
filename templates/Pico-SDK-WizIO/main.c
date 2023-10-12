/*
    PlatformIO ( WizIO 2022 Georgi Angelov )
        TEMPLATE: main.c
*/

#include "pico/stdlib.h"

int main(void)
{  
    gpio_init(PICO_DEFAULT_LED_PIN);
    gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);
    while (true)
    {
        gpio_put(PICO_DEFAULT_LED_PIN, 1);
        sleep_ms(100);
        gpio_put(PICO_DEFAULT_LED_PIN, 0);
        sleep_ms(100);
    }
}