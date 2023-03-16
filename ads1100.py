from micropython import const
from machine import I2C
import time

try:
    from typing_extensions import Literal
except ImportError:
    pass

_ADS1100_DEFAULT_ADDRESS = const(0x48)

_ST_BSY_BIT = const(0b10000000)
_SC_BIT     = const(0b00010000)
_DR_BIT     = const(0b00001100)
_PGA_BIT    = const(0b00000011)

_DATA_RATE = (128, 32, 16, 8)

_GAINS = (1, 2, 4, 8)

_MIN_CODE = {128: -2048, 32: -8192, 16: -16384, 8: -32768}

class ADS1100:
    """Driver for the ADS1100 ADC Converter."""

    CONTINUOUS = const(0)
    SINGLE =const(1)

    # Global buffer to prevent allocations and heap fragmentation.
    # Note this is not thread-safe or re-entrant by design!
    _BUFFER = bytearray(3)

    def __init__(
        self,
        i2c: I2C,
        address: int=_ADS1100_DEFAULT_ADDRESS,
        reference_voltage: float=3.3,
        pressure_ratio: int=2
    ) -> None:
        self._i2c = i2c
        self._addr = address
        self._reference_voltage = reference_voltage
        self._pressure_ratio = pressure_ratio
        self._config = 0x8C
        self._mode = self.CONTINUOUS
        self._rate = 8
        self._gain = 1

    @property
    def value(self) -> int | None:
        '''Read the adc value detected by the ads1100.'''
        self._i2c.writeto(self._addr, self._config.to_bytes(1, 'big'))
        time.sleep(0.1)
        self._read()
        self._config = self._BUFFER[2]
        if (
            self._config & _SC_BIT == 0
            or (
                self._config & _SC_BIT > 0
                and self._config & _ST_BSY_BIT == 0
            )
        ):
            return ((self._BUFFER[0] << 8) | (self._BUFFER[1])) & 0xFFFF
        return None

    @property
    def voltage(self) -> float:
        '''The voltage value computed from the adc value.'''
        voltage = 0
        value = self.value
        if value is not None:
            voltage = (
                (
                    (value / (-1 * _MIN_CODE.get(self._rate) * self._gain))
                    * self._reference_voltage
                )
                * self._pressure_ratio
            )
        return voltage

    @property
    def mode(self) -> Literal[0, 1]:
        '''The conversion mode of the ads1100'''
        return self._mode

    @mode.setter
    def mode(self, mode: Literal[0, 1]) -> None:
        self._mode = mode
        self._config = (self._config & (~_SC_BIT)) | (mode << 4)
        self._i2c.writeto(self._addr, self._config.to_bytes(1, 'big'))

    @property
    def rate(self) -> Literal[128, 32, 16, 8]:
        """The rate of the ads1100.
        Should be a value of 8, 16, 32, or 128.
        """
        return self._rate

    @rate.setter
    def rate(self, data_rate) -> None:
        if data_rate not in _DATA_RATE:
            raise ValueError(
                "Rate should be one of the following values: {0}".format(
                    _DATA_RATE
                )
            )
        self._rate = data_rate
        self._config = (self._config & (~_DR_BIT)) | \
                       (_DATA_RATE.index(data_rate) << 2)
        self._i2c.writeto(self._addr, self._config.to_bytes(1, 'big'))

    @property
    def gain(self) -> Literal[1, 2, 4, 8]:
        '''The gain of the ads1100.
        Should be a value of 1, 2, 4, or 8.
        '''
        return self._gain

    @gain.setter
    def gain(self, gain) -> None:
        if gain not in _GAINS:
            raise ValueError(
                "Gain should be one of the following values: {0}".format(_GAINS)
            )
        self._gain = gain
        self._config = (self._config & (~_PGA_BIT)) | \
                       _GAINS.index(gain)
        self._i2c.writeto(self._addr, self._config.to_bytes(1, 'big'))

    def _read(self) -> None:
        self._i2c.readfrom_into(self._addr, self._BUFFER)
