import logging
import threading
import time

import numpy as np
import sphero_control
import pygame
from pygame.locals import *


class Tactics(threading.Thread):
    """Sphero Tactics module:
        - Displays the user interface
        - Manage Sphero
        - Hold and switch the tactics
    """

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):

        threading.Thread.__init__(self, group=group, target=target, name=name,
                                  verbose=verbose)
        self.args = args
        self.kwargs = kwargs
        self.threadExit = False

        # Get the Opencv Object
        self.openCv = kwargs['openCv']
        self.sphero = sphero_control.Control()

        self.logger = logging.getLogger('sphero.tactics')

        self.isGameRunning = False

        # Koardinaten aus OpenCv
        self.coordsEnemy = None
        self.coordsMe = None
        self.coordEPol = self.coordEGrad = None
        self.coordMPol = self.coordMGrad = None
        self.danger = False

        # Tactic dictionary
        self.tactics = {1: (self.tactic1, "1. Rausschieben"),
                        2: (self.tactic2, "2. GoHome"),
                        3: (self.tactic3, "3. Kreisen"),
                        4: (self.tactic4, "4. Ausweichen"),
                        0: (self.tactic0, "0. Stop")
                        }
        self.clock = None
        self.waitFor = None
        self.tac2_goToTac = 1
        self.tac3_gotoPunkt = 0
        self.tac3_waitFor = None


    def run(self):
        """
        Start the Sphero main program with main loop
        """
        self.logger.debug('Thread Startet running with %s and %s', self.args, self.kwargs)

        # Init the GUI
        pygame.init()
        screen = pygame.display.set_mode((800, 400))
        self.clock = pygame.time.Clock()

        # Fill background
        background = pygame.Surface(screen.get_size())
        background = background.convert()
        background.fill((250, 250, 250))

        # Display text
        font = pygame.font.Font(None, 36)
        text = font.render("Sphero TEAM 1", 1, (10, 10, 10))
        textpos = text.get_rect()
        textpos.centerx = background.get_rect().centerx
        background.blit(text, textpos)

        # Blit everything to the screen
        screen.blit(background, (0, 0))
        pygame.display.flip()

        self.actTactic = 0
        # Main Tactic loop
        while (not self.threadExit):
            background.fill((250, 250, 250))

            # Get Coordinates form the OpenCv Thread
            coordsEnemy = self.openCv.coordsEnemy
            coordsMe = self.openCv.coordsMe

            speedMe = self.openCv.speedMe
            speedEnemy = self.openCv.speedEnemy

            directionMe = self.openCv.directionMe
            directionEnemy = self.openCv.directionEnemy

            if self.isGameRunning:
                text = font.render("Tactic: " + self.tactics[self.actTactic][1], 1, (10, 10, 10))
            else:
                text = font.render("Sphero Team 1", 1, (10, 10, 10))

            textpos = text.get_rect()
            textpos.centerx = background.get_rect().centerx
            background.blit(text, textpos)

            if self.isGameOver():
                background.blit(font.render("Spiel Ende!", 1, (0, 255, 0)), (40, 300))

            # background.blit(font.render("PositionMe:" + str(coordsMe), 1, (10, 10, 10)), (40,40))
            # background.blit(font.render("PositionEnemy:" + str(coordsEnemy), 1, (10, 10, 10)), (40,60))

            # background.blit(font.render("DirectionEnemy:" + str(directionEnemy), 1, (10, 10, 10)), (40,90))
            # background.blit(font.render("SpeedEnemy:" + str(speedEnemy), 1, (10, 10, 10)), (40,110))

            background.blit(font.render("Spiel Starten : Leertaste", 1, (10, 10, 10)), (400, 40))
            background.blit(font.render("Connect         : 1 / 2", 1, (10, 10, 10)), (400, 60))
            background.blit(font.render("Spiel Stop     : Return", 1, (10, 10, 10)), (400, 80))
            background.blit(font.render("SpheroSteuern: Pfeiltasten", 1, (10, 10, 10)), (400, 100))
            background.blit(font.render("Beenden        : ESC", 1, (10, 10, 10)), (400, 120))

            # Calculate Polar coordinates
            if coordsEnemy:
                self.coordEPol, self.coordEGrad = cart2pol(coordsEnemy[0], coordsEnemy[1])
            if coordsMe:
                self.coordMPol, self.coordMGrad = cart2pol(coordsMe[0], coordsMe[1])

            # Read the GUI key events
            for event in pygame.event.get():
                if not hasattr(event, 'key') or (event.type == KEYUP): continue
                down = event.type == KEYDOWN  # key down or up?

                # Game Start
                if event.key == K_SPACE:
                    self.logger.error("Game Start")
                    self.actTactic = 1
                    self.isGameRunning = True

                # Game Stop
                elif event.key == K_RETURN:
                    self.sphero.stop()
                    self.isGameRunning = False

                # Change Tactic manual
                elif event.key == K_a:
                    self.actTactic = 0
                elif event.key == K_s:
                    self.actTactic = 1
                elif event.key == K_d:
                    self.actTactic = 2

                # Control Sphero manual
                elif event.key == K_RIGHT:
                    self.sphero.roll(35, 0)
                elif event.key == K_LEFT:
                    self.sphero.roll(35, 180)
                elif event.key == K_UP:
                    self.sphero.roll(35, 270)
                elif event.key == K_DOWN:
                    self.sphero.roll(35, 90)

                # Connect to Sphero 1 and set game settings
                elif event.key == K_1:
                    self.sphero.connect(0)
                    self.sphero.setColor(2)
                    self.sphero.setBackled(True)
                    self.sphero.setRoataionRate(255)
                # Connect to Sphero 2 and set game settings
                elif event.key == K_2:
                    self.sphero.connect(1)
                    self.sphero.setColor(2)
                    self.sphero.setBackled(True)
                    self.sphero.setRoataionRate(255)
                # Change Sphero color - Red
                elif event.key == K_8:
                    self.sphero.setColor(0)
                # Change Sphero color - Green
                elif event.key == K_9:
                    self.sphero.setColor(1)
                # Change Sphero color - Off
                elif event.key == K_0:
                    self.sphero.setColor(2)

                # Disable stabilization system
                elif event.key == K_3:
                    self.sphero.setStabilation(False)
                # Set new Heading - to set the right direction of Sphero
                elif event.key == K_4:
                    self.sphero.setHeading(0)
                # Enable stabilization system
                elif event.key == K_5:
                    self.sphero.setStabilation(True)

                # Game End
                elif event.key == K_ESCAPE:
                    self.threadExit = True

            # Call the current tactic if game is running
            if self.isGameRunning:

                if self.isGameOver():
                    self.tactic0()
                    self.actTactic = 0
                    self.isGameRunning = False

                else:
                    # Call tactic
                    self.tactics[self.actTactic][0]()

            # Display updated GUI
            screen.blit(background, (0, 0))
            pygame.display.flip()

        # Tactic / Game loop exit - Disconnect Sphero
        self.sphero.disconnect()

    def tactic0(self):
        """
        Tactic 0 - Stop Sphero
        """
        self.sphero.stop()

    def tactic1(self):
        """
        Tactic 1 Rausschieben
        """
        # me weiter aussen als gegener -> taktic goHome()
        # sonst weiter schieben

        # Get coordinates form OpenCv thread if available
        if self.openCv.coordsEnemy and self.openCv.coordsMe:
            coordsEnemy = self.openCv.coordsEnemy
            coordsMe = self.openCv.coordsMe
        gotoGrad = 0

        if coordsEnemy and coordsMe:
            # Calculate the direction and angle to the target position
            coordRad, coordGrad = cart2pol((coordsMe[0] - coordsEnemy[0]), (coordsMe[1] - coordsEnemy[1]))
            if coordGrad >= 180:
                gotoGrad = coordGrad - 180
            else:
                gotoGrad = coordGrad + 180

            # Speed up if near Target
            if coordRad >= 50:
                pass
                self.sphero.roll(60, np.abs(gotoGrad - 360))
            else:
                pass
                self.sphero.roll(150, np.abs(gotoGrad - 360))

            # If your Sphere is more outside than the Target - Change Tactic
            if self.coordMPol > self.coordEPol:
                self.actTactic = 2


    def tactic2(self):
        """
        Tactic 2: Go to Home
        """

        # Call go to Home function - Returns True if Home is reached
        if self.goToHome():
            # When Home is reached - Wait for 1.4 sec than switch to new Tactic
            if self.waitFor is None:
                self.waitFor = int(time.time() * 1000) + 1400

            # Time wait finish: Switch to new Tactic
            elif int(time.time() * 1000) >= self.waitFor:
                self.waitFor = None

                # Switch each Time between the two tactics
                if self.tac2_goToTac == 3:
                    self.actTactic = 1
                    self.tac2_goToTac = 1
                else:
                    self.actTactic = 3
                    self.tac3_gotoPunkt = 0
                    self.tac2_goToTac = 3

        # Home not reached
        else:
            self.waitFor = None

    def tactic3(self):
        """
        Tactic 3: Kreisen
        """

        # Points form the Circle to reache
        kreisPunkte = ((0, 60), (-60, 0), (0, -60), (60, 0))

        # Check if position is available
        if self.openCv.coordsMe:
            coordsMe = self.openCv.coordsMe

            # Go to circle position and if it near enough go to next position
            if self.goToPosition(coordsMe, kreisPunkte[self.tac3_gotoPunkt], 70, 50):
                # Go to next circle position
                self.tac3_gotoPunkt = (self.tac3_gotoPunkt + 1) % 4

                # Do Circling for 5.5 sec then change tactic
        if self.tac3_waitFor is None:
            self.tac3_waitFor = int(time.time() * 1000) + 5500

        # Timer end - go to new tactic
        elif int(time.time() * 1000) >= self.tac3_waitFor:
            self.tac3_waitFor = None
            self.actTactic = 1


    def tactic4(self):
        """
        Tactic 4: Ausweichen wenn gegner mit voller geschwindigkeit kommt, aufpassen auf die Raender  30 > r < 70
        """
        pass

    def goToPosition(self, coordXY, coordTargetXY, speed, abstand):
        """
        Go to Position
        :param speed: set moving speed
        :param abstand: The distance to the target to be reached 
        :returns True - if Target is reached
        """
        gotoGrad = 0

        # Calculate direction and distance to target
        coordRad, coordGrad = cart2pol((coordXY[0] - coordTargetXY[0]), (coordXY[1] - coordTargetXY[1]))
        if coordGrad >= 180:
            gotoGrad = coordGrad - 180
        else:
            gotoGrad = coordGrad + 180

        # Target reached?
        if coordRad >= abstand:
            self.sphero.roll(speed, np.abs(gotoGrad - 360))
            return False

        return True


    def goToHome(self):
        """
        Go to Home Position (0,0)
        """
        gotoGrad = 0
        # Check distance to Home to set the speed
        if self.coordMPol <= 30:
            speed = 20

        elif self.coordMPol <= 60:
            speed = 40

        else:
            speed = 125

        #
        if self.coordMGrad >= 180:
            gotoGrad = self.coordMGrad - 180
        else:
            gotoGrad = self.coordMGrad + 180

        # Start breaking if distance is close and set home reached
        if self.coordMPol > 20:
            self.sphero.roll(speed, np.abs(gotoGrad - 360))
            return False
        else:
            self.sphero.stop()
            return True


    def isGameOver(self):
        """
        Check if Game is over - One of the Spheros out of the circle
        """

        # Check if coordinates are available
        if self.coordMPol is not None and self.coordEPol is not None:
            # Set Danger Zone
            if self.coordMPol >= 70:
                self.danger = True

            return ((self.coordMPol > 87) or (self.coordEPol > 87))


def cart2pol(x, y):
    """
    Calculate Polar coordinates
    """
    rho = np.sqrt(x ** 2 + y ** 2)
    phi = np.degrees(np.arctan2(y, x))
    if phi < 0:
        phi += 360

    return (int(rho), int(phi))


def pol2cart(rho, phi):
    """
    Calculate x,y coordinates form Polar
    """
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return (x, y)


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    tac = Tactics()


if __name__ == '__main__':
    main()


