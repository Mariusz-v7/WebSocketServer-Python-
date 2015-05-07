def multibyteval(bytes, order=0):
    val = 0
    for i, byte in enumerate(bytes):
        if order == 0:
            bitshift = 8 * (len(bytes) - i - 1)
        else:
            bitshift = 8 * i

        val |= byte << bitshift

    return val

def multibytetoarray(value, order=0):
    mask = 0xFF
    arr = bytearray()

    i = 0
    while value != 0:
        byte = value & mask
        value &= ~mask
        mask <<= 8
        byte >>= (8 * i)
        arr.append(byte)
        i += 1

    if order == 0:
        arr.reverse()

    return arr

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
    # reversed
    for i, di in enumerate(datain):
        v = multibyteval(di, 1)
        if v != dataout_reversed[i]:
            test_passed = False

    if test_passed:
        print 'multibyteval function is ok'
    else:
        print 'multibyteval function is not ok'

    datain = [
        0x12345679, 0x9900001112, 0x5051
    ]
    dataout = [
        [0x12, 0x34, 0x56, 0x79], [0x99, 0x00, 0x00, 0x11, 0x12], [0x50, 0x51]
    ]
    dataout_reversed = [
        [0x79, 0x56, 0x34, 0x12], [0x12, 0x11, 0x00, 0x00, 0x99], [0x51, 0x50]
    ]

    test_passed = True
    for i, di in enumerate(datain):
        v = multibytetoarray(di)

        subtest_passed = True
        for j, byte in enumerate(dataout[i]):
            if byte != v[j]:
                subtest_passed = False

        if not subtest_passed:
            test_passed = False

    # reversed
    for i, di in enumerate(datain):
        v = multibytetoarray(di, 1)

        subtest_passed = True
        for j, byte in enumerate(dataout_reversed[i]):
            if byte != v[j]:
                subtest_passed = False

        if not subtest_passed:
            test_passed = False
    if test_passed:
        print 'multibytetoarray function is ok'
    else:
        print 'multibytearray function is not ok'
