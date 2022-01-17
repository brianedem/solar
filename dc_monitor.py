import ADS1256

adc = ADS1256.adc(0,0)

ib_offset = 4.9650

def dummy():
    return  adc.read_data(ADS1256.PSEL0 | ADS1256.NSEL1)

def knob():
    return  adc.read_data(ADS1256.PSEL0 | ADS1256.NCOM)

def light():
    return  adc.read_data(ADS1256.PSEL1 | ADS1256.NCOM)

def ibattery() :
        # 2:1 resistive voltage scaling, ~5V offset@0A, 7V@50A
    v_sensor = adc.read_data(ADS1256.PSEL3 | ADS1256.NSEL2)*2
    v_scaled = v_sensor - ib_offset
    return v_scaled * (50/2)

def isolar() :
        # 10V@100A, max solar current is 6000W/400V=15A -> 1.5V
    v_sensor = adc.read_data(ADS1256.PSEL5 | ADS1256.NSEL4)
    return v_sensor * 100/10

def vbus() :
        # 2:1 voltage scaling, 10V@500V, 400V->8V
    v_sensor = adc.read_data(ADS1256.PSEL6 | ADS1256.NCOM)*2
    return v_sensor * 500/20
