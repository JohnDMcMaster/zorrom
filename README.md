Zorro's (mask) ROM

Mask ROM utilities to convert between physical and word representation. For example, a ROM chip image typed as a 0/1s .txt file can be converted into a .bin file.

Tools that can produce this format include:
* rompar save
* bitract
* django-monkeys using tools/db2txt.py

# Arch

## d8041ah (NEC)

Notes:
  * Technology: contact ROM
  * Polarity: contact as 1
  * Orientation: "NEC D8041AH" should be on the left such that address decoding circuitry is to the right and bottom

## m5l8042 (Mitsubishi)

Notes:
  * Technology: contact ROM
  * Polarity: FIXME
  * Orientation: FIXME


## mb8623x (Fujitsu)

Notes:
  * Technology: contact ROM
  * Polarity: FIXME
  * Orientation: FIXME

## pic1670 (Microchip/GI)

Notes:
  * Technology: implant NOR ROM
  * Polarity: etched bit 1 (apperas darker)
  * Orientation: main decoding circuitry at left
  * First and last column row groups are not bits (appears as 10 bits but is 8)
  * Reference: https://siliconpr0n.org/map/apple/pic1670-adb-turbo/s1-3-dash-15_mit20x/

