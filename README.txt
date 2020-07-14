Zorro's (mask) ROM
Mask ROM capture utilities

This ingests .txt files with 1/0s laid out in a grid as if overload into a die photo
Tools that can produce this format include:
-django-monkeys using tools/db2txt.py
-rompar save 

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
  * See: https://siliconpr0n.org/map/apple/pic1670-adb-turbo/s1-3-dash-15_mit20x/

