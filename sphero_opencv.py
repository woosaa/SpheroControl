# coding=utf-8
import logging
import json
import os
import threading
import time
import numpy as np
import cv2


# OpenCV config parameter
CV_CAP_PROP_FRAME_WIDTH = 3
CV_CAP_PROP_FRAME_HEIGHT = 4
CV_CAP_PROP_FRAME_RATE = 6

class Opencv(threading.Thread):
    """
    provides the connection to opencv
    """
    def __init__(self, group=None, target=None, name='Thread-Opencv-',
                 args=(), kwargs=None, verbose=None):
        threading.Thread.__init__(self, group=group, target=target, name=name, verbose=verbose)

        self.threadExit = False
        self.args = args
        self.kwargs = kwargs

        self.logger = logging.getLogger('sphero.opencv')
        self.enemy = loadConfig('enemy')
        self.me = loadConfig('me')
        self.homo = loadConfig('homo')
        self.frame = None
        self.cap = cv2.VideoCapture(0)
        self.cap.set(CV_CAP_PROP_FRAME_WIDTH, 800)
        self.cap.set(CV_CAP_PROP_FRAME_HEIGHT, 600)
        # Homography Data
        self.isHomo = False
        self.isCalibrateDist = True
        self.proportion = 0
        self.homoGotClick = False
        self.homoXYClick = None
        self.homoXYValues = None
        self.homoXYtmp = None
        self.homoXY = []
        self.homoString = ""
        self.value = ""
        self.frameCounter = None
        self.ring = np.array([[19, 193], [220, 20], [452, 192], [248, 416], [81, 358], [107, 56]])
        # Thread Data
        self.coordsMe = None
        self.coordsEnemy = None
        self.directionMe = None
        self.directionEnemy = None
        # Speed Data
        self.speedMe = None
        self.speedEnemy = None


    def run(self):
        """
        Start the Sphero main program with main loop
        """
        self.logger.info("Thread Opencv Started")

        # Call config in config parameter is set
        if self.kwargs['config']:
            self.openCVconfig()
            return

        frameDistance = 8
        frameCounter = 0
        while not self.threadExit:

            # Capture frame-by-frame
            ret, frame = self.cap.read()
            self.frame = frame[132:571, 170:672]

            # get direction and direction of own Sphero
            posMe = self.getPosition(1)
            posEnemy = self.getPosition(0)

            # take first frame at start and furthermore every 8 frame
            if frameCounter % frameDistance == 0:
                time1 = time.time()
                pointMe = posMe
            elif frameCounter % frameDistance == frameDistance - 1:
                time2 = time.time()
                pointMe2 = posMe

                #
                if (pointMe is not None) and (pointMe2 is not None):
                    direction = calcDirection(pointMe[0], pointMe[1], pointMe2[0], pointMe2[1])
                    speed = calculateSpeed(self, pointMe[0], pointMe[1], pointMe2[0], pointMe2[1], time1, time2)
                    self.speedMe = speed
                    self.directionMe = direction

            # get direction and direction of enemy Sphero
            if frameCounter % frameDistance == 0:
                timeEnemy1 = time.time()
                pointEnemy = self.getPosition(0)
            elif frameCounter % frameDistance == frameDistance - 1:
                timeEnemy2 = time.time()
                pointEnemy2 = self.getPosition(0)

                if (pointEnemy is not None) and (pointEnemy2 is not None) \
                        and (pointMe is not None) and (pointMe2 is not None):
                    direction = calcDirection(pointEnemy[0], pointEnemy[1], pointEnemy2[0], pointEnemy2[1])
                    speed = calculateSpeed(self, pointMe[0], pointMe[1], pointMe2[0], pointMe[1], timeEnemy1,
                                           timeEnemy2)
                    self.speedEnemy = speed
                    self.directionEnemy = direction

            frameCounter += 1

            # Display the resulting frame
            cv2.imshow('frame', self.frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # When everything done, release the capture
        self.cap.release()
        cv2.destroyAllWindows()

    def nothing(x, y=None):
        pass

    def getPerspectivePosition(self, point):
        """
        Calculate World-Coordinates for a given Point in Picture-Coordinates
        :param point: Point in Picture-Coordinates
        :return: list of x and y World-Coordinates
        """

        if point is not None:
            c = np.array([np.array([[point[0], point[1]]], dtype='float32')])
            h = np.array(self.homo['homo'], dtype=np.float32)

            tmpc = cv2.perspectiveTransform(c, h)
            return (tmpc[0][0][0], tmpc[0][0][1])

        return None

    def getPosition(self, enemy=0):
        """
        Get the Position  of given Sphero
        :param enemy: Set enemy == 0 for Enemy Sphero and 1 for own Sphero
        :return: list of x-Position, y-Position and radius
        """

        if enemy == 0:
            config = self.enemy
        else:
            config = self.me

        points = None

        lowerColor = np.array([config['cLowH'], config['cLowS'], config['cLowV']])
        upperColor = np.array([config['cHighH'], config['cHighS'], config['cHighV']])

        imgHSV = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(imgHSV, lowerColor, upperColor)

        mask[mask == 0] = 0
        # Bitwise-AND mask and original image
        res = cv2.bitwise_and(self.frame, self.frame, mask=mask)
        kernel = np.ones((15, 15), np.uint8)

        # erosion = cv2.erode(mask,kernel,iterations = 1)
        mask = cv2.GaussianBlur(mask, (15, 15), 0)

        mask = cv2.erode(mask, kernel)
        mask = cv2.dilate(mask, kernel)

        coord = None
        points = np.dstack(np.where(mask > 0)).astype(np.float32)

        if len(points[0]) > 0:
            center, radius = cv2.minEnclosingCircle(points)

            #if center is not None and radius is not None:
            # draw this circle
            cv2.circle(self.frame, (int(center[1]), int(center[0])), 2, (0, 0, 255), 3)
            coord = ([int(center[1]), int(center[0]), radius])

            if enemy == 0:
                self.coordsEnemy = self.getPerspectivePosition(coord)
            else:
                self.coordsMe = self.getPerspectivePosition(coord)

            return (int(center[1]), int(center[0]), radius)

        return None

    def getMouseclick(self, event, x, y, flags, param):
        """
        Print current Mouse position
        :param event: current Mouse-Event
        :param x: X-Value of Mouseclk
        :param y: Y-Value of Mouseclk
        :return: no return
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            print(x)
            print(y)

    def openCVconfig(self):
        """
        Camera and Homography Configuration menu
        :return: no return
        """
        cv2.namedWindow('image')
        config = {}
        sphere = {}
        # create trackbars for color change
        cv2.createTrackbar('LowH', 'image', 0, 255, self.nothing)
        cv2.createTrackbar('HighH', 'image', 0, 255, self.nothing)

        cv2.createTrackbar('LowS', 'image', 0, 255, self.nothing)
        cv2.createTrackbar('HighS', 'image', 0, 255, self.nothing)

        cv2.createTrackbar('LowV', 'image', 0, 255, self.nothing)
        cv2.createTrackbar('HighV', 'image', 0, 255, self.nothing)

        cv2.createTrackbar('minRadius', 'image', 0, 255, self.nothing)
        cv2.createTrackbar('maxRadius', 'image', 0, 255, self.nothing)

        homoValue = ""
        homoXWorld = None
        while (True):
            # get current positions of four trackbars
            config['cLowH'] = cv2.getTrackbarPos('LowH', 'image')
            config['cHighH'] = cv2.getTrackbarPos('HighH', 'image')

            config['cLowS'] = cv2.getTrackbarPos('LowS', 'image')
            config['cHighS'] = cv2.getTrackbarPos('HighS', 'image')

            config['cLowV'] = cv2.getTrackbarPos('LowV', 'image')
            config['cHighV'] = cv2.getTrackbarPos('HighV', 'image')

            config['minRadius'] = cv2.getTrackbarPos('minRadius', 'image')
            config['maxRadius'] = cv2.getTrackbarPos('maxRadius', 'image')

            # define range of color in HSV
            lowerColor = np.array([config['cLowH'], config['cLowS'], config['cLowV']])
            upperColor = np.array([config['cHighH'], config['cHighS'], config['cHighV']])

            # Capture frame-by-frame
            ret, frame = self.cap.read()
            self.frame = frame[132:571, 170:672]
            #ret, self.frame = self.cap.read()

            #self.frame = img[200:400, 100:300] # Crop from x, y, w, h -> 100, 200, 300, 400
            # NOTE: its img[y: y + h, x: x + w] and *not* img[x: x + w, y: y + h]

            if self.isHomo:
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(self.frame, self.homoString, (10, 40), font, 2, (255, 255, 255))

                cv2.imshow('frame', self.frame)

            else:
                # Our operations on the frame come here
                imgHSV = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)

                cv2.setMouseCallback('frame', self.getMouseclick)

                # Threshold the HSV image to get only colors
                mask = cv2.inRange(imgHSV, lowerColor, upperColor)

                # Bitwise-AND mask and original image
                res = cv2.bitwise_and(self.frame, self.frame, mask=mask)

                # Display the resulting frame
                #cv2.imshow('frame', frame)

                #print self.getPerspectivePosition(self.getPosition(0))
                sphere = self.getPosition(1)
                sphereEnemy = self.getPosition(0)

                retval = cv2.fitEllipse(self.ring)

                cv2.ellipse(self.frame, retval, (0, 255, 0), 2)

                if sphere is not None:
                    #points = np.dstack(np.where(mask>0)).astype(np.float32)
                    #inside = cv.PointPolygonTest(retval, (sphere['x'], sphere['y']), True)
                    #print inside
                    cv2.circle(self.frame, (sphere[0], sphere[1]), config['minRadius'], (0, 255, 0), 2)
                    cv2.circle(self.frame, (sphere[0], sphere[1]), config['maxRadius'], (0, 255, 0), 2)

                if sphereEnemy is not None:
                    cv2.circle(self.frame, (sphereEnemy[0], sphereEnemy[1]), config['minRadius'], (255, 0, 0), 2)
                    cv2.circle(self.frame, (sphereEnemy[0], sphereEnemy[1]), config['maxRadius'], (255, 0, 0), 2)

                cv2.imshow('Maske', mask)
                cv2.imshow('Kombiniert', res)
                cv2.imshow('frame', self.frame)
                # cv2.imshow('res',res)
            key = cv2.waitKey(1) & 0xFF
            #Ende

            if not self.isHomo:
                if key == ord('q'):
                    break
                #Save 1
                if key == ord('2'):
                    saveConfig('me', config)
                #Save 2
                if key == ord('0'):
                    saveConfig('enemy', config)
                #Load 1
                if key == ord('1'):
                    config = loadConfig('me')
                    sphere = self.getPosition()
                    cv2.setTrackbarPos('LowH', 'image', config['cLowH'])
                    cv2.setTrackbarPos('HighH', 'image', config['cHighH'])

                    cv2.setTrackbarPos('LowS', 'image', config['cLowS'])
                    cv2.setTrackbarPos('HighS', 'image', config['cHighS'])

                    cv2.setTrackbarPos('LowV', 'image', config['cLowV'])
                    cv2.setTrackbarPos('HighV', 'image', config['cHighV'])

                    cv2.setTrackbarPos('minRadius', 'image', config['minRadius'])
                    cv2.setTrackbarPos('maxRadius', 'image', config['maxRadius'])

                #Load 2
                if key == ord('9'):
                    config = loadConfig('enemy')
                    cv2.setTrackbarPos('LowH', 'image', config['cLowH'])
                    cv2.setTrackbarPos('HighH', 'image', config['cHighH'])

                    cv2.setTrackbarPos('LowS', 'image', config['cLowS'])
                    cv2.setTrackbarPos('HighS', 'image', config['cHighS'])

                    cv2.setTrackbarPos('LowV', 'image', config['cLowV'])
                    cv2.setTrackbarPos('HighV', 'image', config['cHighV'])

                    cv2.setTrackbarPos('minRadius', 'image', config['minRadius'])
                    cv2.setTrackbarPos('maxRadius', 'image', config['maxRadius'])

                #config Homographie
                if key == ord('h'):
                    self.isHomo = True
                    cv2.setMouseCallback('frame', self.getMousePos, param={'a': True})
                    self.homoString = "Homography Menu"
                    cv2.destroyWindow('Maske')
                    cv2.destroyWindow('Kombiniert')

            else:
                #If Homography mode is on!

                # exit
                if key == ord('q'):
                    break

                # Got Click for Homography Calculation
                if self.homoGotClick:
                    # get next number (ascii 48-57 -> dez 0-9)
                    if key in (np.arange(45, 58)):
                        homoValue += str(chr(key))
                        self.homoString = "GET Value:  " + homoValue

                    # backspace - Delete Value
                    if key == 8:
                        homoValue = ""

                    # Enter - set current value
                    if key == 10 or key == 13:
                        if homoXWorld is None:
                            homoXWorld = int(homoValue)
                            homoValue = ""
                            self.homoString = "GET Y Value:  "
                        else:
                            coardinaten = [self.homoXYtmp['picX'], self.homoXYtmp['picY'], homoXWorld, int(homoValue)]
                            self.homoXY.append(coardinaten)

                            self.homoString = "Next Point "
                            homoXWorld = None
                            homoValue = ""
                            self.homoGotClick = False
                            print("Homo got Points: ", coardinaten)

                            # calculate Homography if min. nine Points have been collected
                            if len(self.homoXY) >= 9:
                                cv2.setMouseCallback('frame', self.getMousePos, param={'a': False})
                                self.isHomo = False
                                self.logger.info("Homo: Start Calc")
                                print(self.homoXY)

                                src_pts = np.float32([[p[0], p[1]] for p in self.homoXY])
                                dst_pts = np.float32([[p[2], p[3]] for p in self.homoXY])
                                H = cv2.findHomography(src_pts, dst_pts)[0]
                                saveHomo('homo', H)
                                self.homo = H

                                # Calibrate Distance Pixel/Centimeter
                                if self.isCalibrateDist:
                                    self.isCalibrateDist = False

                                    if src_pts is not None and dst_pts is not None:
                                        pixelDist = np.sqrt(np.power(src_pts[0][0], 2) + np.power(src_pts[0][1], 2))
                                        cmDist = np.sqrt(np.power(dst_pts[0][0], 2) + np.power(dst_pts[0][1], 2))

                                        self.proportion = pixelDist / cmDist

        # When everything done, release the capture
        self.cap.release()
        cv2.destroyAllWindows()

    def getMousePos(self, event, x, y, flags, param):
        """
        mouse callback function for Homography-mode
        :param event: current Mouse-Event
        :param x: X-Value of Mouseclk
        :param y: Y-Value of Mouseclk
        :param param: Value should be true if and only if Mouse-Callback is needed
        """
        if event == cv2.EVENT_LBUTTONDOWN and param['a'] and self.homoGotClick is True:
            self.homoGotClick = True
            # save x and y Position
            self.homoXYtmp = {'picX': x, 'picY': y}
            self.homoString = "GET X Value:  "

def main():
    """
    Main Method
    """
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    c = Opencv()
    c.run()

def calcDirection(x0, y1, x2, y2):
    """
    (NOT WORKING) Calculate angle between two given points in Degree
    :param x1: X-Value of first Point
    :param y1: Y-Value of first Point
    :param x2: X-Value of second Point
    :param y2: Y-Value of second Point
    :return: current Direction of Sphero in Degree
    """
    # Distance moved between points
    distX = (x2 - x1)
    distY = (y2 - y1)

    ret = None
    if distX != 0:
        # calculate Angle of movement
        ret = np.degrees(np.arctan(distY / distX))

        # check 0° or 180°
        if distX < 0 and distY == 0:
            ret = 180
    else:
        # has Sphero moved or not
        if distY != 0:
            ret = 90

    # add 360 if Angle is negative to get a positive result
    if ret < 0:
        if ret is None:
            ret = None
        else:
            ret += 360
    return ret


def calculateSpeed(self, x1, y1, x2, y2, time1, time2):
    """
    (NOT WORKING) Calculate Speed based on two given Points
    :param x1: X-Value of first Point
    :param y1: Y-Value of first Point
    :param x2: X-Value of second Point
    :param y2: Y-Value of second Point
    :param time1: Timestamp of first frame
    :param time2: Timestamp of second frame
    :return: current Speed in cm/s (int)
    """

    # calculate vector between points
    d_x = x2
    d_x -= x1
    d_y = y2
    d_y -= y1

    # calculate lengths of Distancevector
    distance = np.power(d_x, 2)
    distance += np.power(d_y, 2)
    distance = np.sqrt(distance)
    distance /= self.proportion

    # calculate difference between Timestamps
    time = time1
    time -= time2
    time /= 1000

    # calculate Speed in cm/s
    speed = distance
    speed /= float(time)

    return speed


def saveConfig(name, config):
    """
    save Configuration in json File
    :param name: Filename
    :param config: Path to Configuration-file
    :return: no return
    """
    # Set Path
    path = 'config/' + name + '.json'
    # dump json-File
    with open(path, 'wb') as fp:
        json.dump(config, fp)


def loadConfig(name):
    """
    load Configuration from json
    :param name: Filename
    :return: Configuration-Data
    """
    # Set Path
    path = 'config/' + name + '.json'
    # load json-File
    if os.path.isfile(path):
        with open(path, 'rb') as fp:
            data = json.load(fp)

        return data
    return None


def saveHomo(name, homo):
    """
    save Homography Configuration in json File
    :param name: Filename
    :param homo: calculated Homography
    :return: no return
    """
    # Set Path
    path = 'config/' + name + '.json'
    # dump json-File
    with open(path, 'wb') as fp:
        json.dump({"homo": homo.tolist()}, fp)


if __name__ == '__main__':
    main()
