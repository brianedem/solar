import ADS1256

adc = ADS1256.adc(0,0)

ibat_offset = 124.0
vbus_offset = 2.0

def dummy():
    return  adc.read_data(ADS1256.PSEL0 | ADS1256.NSEL1)

def knob():
    return  adc.read_data(ADS1256.PSEL0 | ADS1256.NCOM)

def light():
    return  adc.read_data(ADS1256.PSEL1 | ADS1256.NCOM)

def ibattery() :
        # 2:1 resistive voltage scaling, ~5V offset@0A, 7V@50A
    v_sensor = adc.read_data(ADS1256.PSEL3 | ADS1256.NSEL2)*2
    return v_sensor * (50/2) - ibat_offset

def isolar() :
        # 10V@100A, max solar current is 6000W/400V=15A -> 1.5V
    v_sensor = adc.read_data(ADS1256.PSEL5 | ADS1256.NSEL4)
    if v_sensor < 0 :
        return 0.0
    else :
        return v_sensor * 100/10

def vbus() :
        # 2:1 voltage scaling, 10V@500V, 400V->8V
    v_sensor = adc.read_data(ADS1256.PSEL6 | ADS1256.NCOM)*2
    if v_sensor < 0 :
        return 0.0
    else :
        return v_sensor * 500/20 - vbus_offset

def test() :
    return adc.read_data(ADS1256.PSEL4 | ADS1256.NCOM)

if __name__=='__main__' :
    import time

    #print measure("dummy")
    print ("knob battery solar bus")
    for i in range(10) :
        print ("%4.2f %5.1f %4.1f %4.0f" % (
                knob(),
                ibattery(),
                isolar(),
                vbus(),
                ))
        time.sleep(1)

    exit()

    first = ibattery()
    print (first)

    min = 10
    max = -10
    avg = 0
    start = time.time()
    for i in range(100) :
        value = ibattery()
        if value < min :
            min = value
        if value > max :
            max = value
        avg += value

    print (min, max, avg/100)
