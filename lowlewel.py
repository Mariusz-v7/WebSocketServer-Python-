def multibyteval(bytes, order=0):
    val = 0
    for i, byte in enumerate(bytes):
        if order == 0:
            bitshift = 8 * (len(bytes) - i - 1)
        else:
            bitshift = 8 * i

        val |= byte << bitshift

    return val

def test():
    datain = [
        [0x80, 0x81, 0x82], [0x91, 0x00, 0x01]
    ]
    dataout = [
        0x808182, 0x910001
    ]
    dataout_reversed = [
        0x828180, 0x010091
    ]

    test_passed = True
    for i, di in enumerate(datain):
        v = multibyteval(di)
        if v != dataout[i]:
            test_passed = False
    #reversed
    for i, di in enumerate(datain):
        v = multibyteval(di, 1)
        if v != dataout_reversed[i]:
            test_passed = False

    if test_passed:
        print 'multibyteval function is ok'
    else:
        print 'multibyteval function is not ok'
