# Development Platform ( IO ) for Raspberry PI

(...)

## FRAMEWORKS
* Raspberry PI RP2040 Pico SDK CMAKE ( as is )
* Raspberry PI RP2040 User Friendly ( WizIO edition )
* Raspberry PI RP2040 Pico microPython
* Raspberry PI RP2040 Pico Arduino ( TODO )
* Raspberry PI 3,4,5 C/C++ Executable
* Raspberry PI 3,4,5 Python Executable
* Raspberry PI 3,4,5 Arduino Executable ( TODO )

## INSТALL 
* Maybe need PC GCC / MinGW installed
* Advanced platform installation - from URL: **https://github.com/Wiz-IO/wizio-RPI**
* Auto clone last pico-sdk ( about 2 minutes, only platform & framework )

## UPDATE
* Delete folder ( update pico-sdk ): .platformio\packages\framework-RPI
* Delete folder ( update platform ): .platformio\platforms\wizio-RPI

## TODO...

Many people asked me: Why did you delete the **wizio-pico** platform<br>
Some even got mad at me...<br>
## My story with RP2040 was as follows
Announced on 21 January 2021...<br>
A month after PI Pico came out I released a port for VSCode/PlatformIO - C/C++ and Arduino, based on Pico SDK<br>
However, the Pico SDK is strategically wrong !<br>
I tried to explain to them ( not just me )<br>
They answered rudely and arrogantly, style: **Who are you to teach us !?**<br>

Аctually I (and others) understood this<br>
- the boss gave an assignment, we took the money, the assignment was completed ... and dot. There is no way to admit our mistakes


The Pico SDK is not structured properly and it becomes complicated to use<br>
**One file - One folder** ?!?! for a handful of source code Cortex M0<br>
It is slow and complex to compile, very difficult to integrate... etc<br>
**If a concept is complicated, it means - small audience, small usage, small profits** right?<br>

OK, I structured the Pico SDK as it should be: <br>
all H - include, src: hal & hi level codes ... nothing else, a simple MAKE handles this<br>
I promoted the platform ... it was a WOW effect !!! C/C++ and Arduino<br>

While I was writing examples for the kids: how to ... I got an idea about WiFi<br>
The idea was to use an SDIO chip ( USB WiFI for PC )<br>
because millions of chips (for PC) have been put into use and have been tested to the maximum and their price is minimal<br>

Searching for a solution I reached WICED Cypress/Broadcom ( full documentation !!! )<br>
but I couldn't find a chip to experiment with, nor do I have a scale to implement<br>
Broadcom!!! so, they are friends with RaspberryPI !!!<br>
I have detailed the RaspberryPI Pico idea/solution<br>
Followed: This is nonsense ... we are working on more surprises<br>
deleted the idea ... the screenshot is a reaction to the above action<br>
OK, no problem<br>

About a year has passed since these events<br>
Surfing the WEB I come across ads: Pico W ( wifi )<br>
to look at what they did ... ?!?!?!?! just as I described, one to one !!!!<br>
- Guys, say: Thanks...<br>
- **Who are you, these are trivial things?** ( in this sense )<br>
- ?!?!<br>

It is not possible for me to know the platform, the chip, the interface and the way it works ... <br>
**I am not an oracle to know all the parameters**<br>
Ok, no problem<br>


