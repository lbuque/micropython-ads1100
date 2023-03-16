# Micropython Module for the ADS1100 ADC Converter

## Example usage:

```python
import time
from machine import I2C, Pin
from ads1100 import ADS1100

i2c0 = I2C(0, scl=Pin(1), sda=Pin(2), freq=400000)
# https://docs.m5stack.com/zh_CN/unit/adc
ads = ADS1100(i2c0, pressure_ratio=4)
ads.mode = ads.CONTINUOUS
ads.rate = 8 #8 16 32 128
ads.gain = 1 # 1 2 4 8

while True:
    print("ADC value: {0}, voltage: {1}".format(ads.value, ads.voltage))
    time.sleep(1)
```
