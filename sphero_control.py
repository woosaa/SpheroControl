import logging

from sphero_driver import sphero_driver


class Control(object):
    """Controls and connects to Sphero.
    Is a more abstract interface to the Sphero library"""


    def __init__(self, openCv=None):
        self.logger = logging.getLogger('sphero.control')
        self.sphero = sphero_driver.Sphero()
        self.openCv = openCv

    def connect(self, mac=None):
        """Connect to Sphero
        mac = 1 - Connect to Sphero 1
        mac = 2 - Connect to Sphero 2
        
        Return: True if connect was successful
        """
        macID= ("68:86:E7:01:5C:6A", "68:86:E7:03:17:7B")
        
        if self.sphero.is_connected:
            return True
        if mac is None:
            ret = self.sphero.connect()
        else:
            ret = self.sphero.connect(macID[mac])

        if not ret:
            self.logger.warning("Not Connected")
        else:
            self.sphero.set_raw_data_strm(40, 1, 0, False)
            self.sphero.start()
            return True
        return False

    def disconnect(self):
        """Disconnect Sphero"""
        if self.sphero.is_connected:
            self.sphero.disconnect()

    def setColor(self, colorId, static=False):
        """Set Spheros color
        :param colorId: 1-Red, 2-Green 3-Off
        :param static: Save color"""
        color = ((255,0,0), (0,255,0), (0,0,0), (255,255,255))
        col = color[colorId]
        if self.sphero.is_connected:
            self.sphero.set_rgb_led(col[0],col[1],col[2],int(static),False)


    def setRoataionRate(self, rate):
        """Set the rotation rate for the new heading
        param: rate: 0 - 255"""

        if self.sphero.is_connected:
            self.sphero.set_rotation_rate(rate,None)
        

    def roll(self,speed, heading):
        """This commands Sphero to roll along the provided vector. Both a
        speed and a heading are required; the latter is considered
        relative to the last calibrated direction. A state Boolean is also
        provided (on or off). The client convention for heading follows the 360
        degrees on a circle, relative to the ball: 0 is straight ahead, 90
        is to the right, 180 is back and 270 is to the left. The valid
        range is 0..359.

        :param speed: 0-255 value representing 0-max speed of the sphero.
        :param heading: heading in degrees from 0 to 359.
        """
        if self.sphero.is_connected:
            self.sphero.roll(speed, heading, 1, None)
        
    def setHeading(self,heading):
        if self.sphero.is_connected:
            self.sphero.set_heading(heading, None)

    def stop(self):
        """Stops Sphero"""
        if self.sphero.is_connected:
            self.sphero.roll(0,0,0,None)
    
    def setStabilation(self, stabilation=True):
        """Enables or disables Spheros stabilizations system
        param: stabilation: bool"""
        if self.sphero.is_connected:
            self.sphero.set_stablization(stabilation, None)
        
    def setBackled(self, brightness):
        """Controls the brightness of Spheros back LED
        param: brightness: 0 - 255"""
        if self.sphero.is_connected:
            self.sphero.set_back_led(brightness, None)
       
def main():
    "Only for Development Tests"
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    cont = Control()

if __name__ == '__main__':
    main()
