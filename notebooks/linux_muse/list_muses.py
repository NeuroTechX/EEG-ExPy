from bluepy.btle import Scanner, DefaultDelegate

class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        pass
#        if isNewDev:
#            print("Discovered device", dev.addr)
#        elif isNewData:
#            print("Received new data from", dev.addr)

def list_muses():
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(10.0)

    muses = list()

    for dev in devices:
        #print("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
        for (adtype, desc, value) in dev.getScanData():
            if desc == "Complete Local Name" and "muse" in value.lower():
                muse_dict = {'address' : dev.addr, 'name' : value}
                muses.append(muse_dict)
                print("Found %s" % (value))
    return muses

if __name__ == "__main__":
    print(list_muses())
