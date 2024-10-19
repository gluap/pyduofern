# Notes on the duofern protocol
- The duofernstick contains an NRF905 microcontroller.
- using rtlsdr, duofern packets can be received and decoded using the command below with rtl-433 (adapted from [here](https://github.com/merbanan/rtl_433/issues/33#issuecomment-715569878)). At first glance the beginning of the packet contains the data and in the end some changing data appears.
- Somehow the command receives data on my desktop but not on my laptop. Possibly on the laptop there is too much interference from the USB hub etc...

```
rtl_433 -s 2.0M -f 434.5M -g 55 -X "n=nrf905,m=FSK_MC_ZEROBIT,s=10,r=100,preamble={10}fd4,invert" -S known |sed s/code/CODE/g
```

Output will look like this: 

```
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
time      : 2024-10-19 16:12:46
model     : nrf905       count     : 1             num_rows  : 1             rows      : 
len       : 305          data      : e3ac43186fCODE4098820200000303201101070100000000000000000000aaad1593b2a326ef8
codes     : {305}e3ac43186fCODE4098820200000303201101070100000000000000000000aaad1593b2a326ef8
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
time      : 2024-10-19 16:12:50
model     : nrf905       count     : 1             num_rows  : 1             rows      : 
len       : 305          data      : e3ac43186fCODE409b21017c5c12042011ff0f210d086400000041641100bc928a7931a12ec18
codes     : {305}e3ac43186fCODE409b21017c5c12042011ff0f210d086400000041641100bc928a7931a12ec18
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
time      : 2024-10-19 16:12:50
model     : nrf905       count     : 1             num_rows  : 1             rows      : 
len       : 267          data      : e3ac43186fCODE409b21017c5c12032011ff0f213a10c800000082c8223fdc0455a
codes     : {267}e3ac43186fCODE409b21017c5c12032011ff0f213a10c800000082c8223fdc0455a
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _  
time      : 2024-10-19 16:12:51
model     : nrf905       count     : 1             num_rows  : 1             rows      : 
len       : 304          data      : e3ac43186fCODE408e43011f5804032011ff0f210d086400000041001100e2ddf57cf12341f9
codes     : {304}e3ac43186fCODE408e43011f5804032011ff0f210d086400000041001100e2ddf57cf12341f9
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
time      : 2024-10-19 16:12:51
model     : nrf905       count     : 1             num_rows  : 1             rows      : 
len       : 305          data      : e3ac43186fCODE408e43011f5804032011ff0f210d086400000041001100e2ddf57cf12341f98
codes     : {305}e3ac43186fCODE408e43011f5804032011ff0f210d086400000041001100e2ddf57cf12341f98
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
time      : 2024-10-19 16:12:51
model     : nrf905       count     : 1             num_rows  : 1             rows      : 
len       : 304          data      : e3ac4318ffffff6fCODE010013f4042011ff0f4000000000000000000000c604313438c273e9
codes     : {304}e3ac4318ffffff6fCODE010013f4042011ff0f4000000000000000000000c604313438c273e9
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
time      : 2024-10-19 16:12:52
model     : nrf905       count     : 1             num_rows  : 1             rows      : 
len       : 304          data      : e3ac43184098826fCODE00ffffff04201101070100000000000000000000d2dc2968ce7b0684
codes     : {304}e3ac43184098826fCODE00ffffff04201101070100000000000000000000d2dc2968ce7b0684
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
```