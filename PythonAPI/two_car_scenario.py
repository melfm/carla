#!/usr/bin/env python

# Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat
# Autonoma de Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import glob
import os
import sys

try:
    sys.path.append(glob.glob('**/*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

import random
import time

import argparse
import logging

try:
    import pygame
    from pygame.locals import K_DOWN
    from pygame.locals import K_LEFT
    from pygame.locals import K_RIGHT
    from pygame.locals import K_SPACE
    from pygame.locals import K_UP
    from pygame.locals import K_a
    from pygame.locals import K_d
    from pygame.locals import K_p
    from pygame.locals import K_q
    from pygame.locals import K_s
    from pygame.locals import K_w
except ImportError:
    raise RuntimeError(
        'cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError(
        'cannot import numpy, make sure numpy package is installed')


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
START_POSITION = carla.Transform(carla.Location(x=180.0, y=199.0, z=40.0))
NPC_START_POSITION = carla.Transform(carla.Location(x=200.0, y=199.0, z=40.0))
CAMERA_POSITION = carla.Transform(carla.Location(x=0.5, z=1.40))


def save_to_disk(image):
    """Save this image to disk (requires PIL installed)."""

    filename = '_images/{:0>6d}_{:s}.png'.format(
        image.frame_number, image.type)

    try:
        from PIL import Image as PImage
    except ImportError:
        raise RuntimeError(
            'cannot import PIL, make sure pillow package is installed')

    image = PImage.frombytes(
        mode='RGBA',
        size=(image.width, image.height),
        data=image.raw_data,
        decoder_name='raw')
    color = image.split()
    image = PImage.merge("RGB", color[2::-1])

    folder = os.path.dirname(filename)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    image.save(filename)


class CarlaGame(object):

    def __init__(self, args):
        self._client = carla.Client(args.host, args.port)
        self._display = None
        self._surface = None
        self._camera = None
        self._vehicle = None
        self._npc_vehicle = None
        self._autopilot_enabled = args.autopilot
        self._is_on_reverse = False

    def _on_loop(self):
        autopilot = self._autopilot_enabled
        control = self._get_keyboard_control(pygame.key.get_pressed())
        if autopilot != self._autopilot_enabled:
            self._vehicle.set_autopilot(autopilot)
            self._autopilot_enabled = autopilot
        if not self._autopilot_enabled:
            self._vehicle.apply_control(control)

        self._npc_vehicle.set_autopilot(True)

    def _get_keyboard_control(self, keys):
        control = carla.VehicleControl()
        if keys[K_LEFT] or keys[K_a]:
            control.steer = -1.0
        if keys[K_RIGHT] or keys[K_d]:
            control.steer = 1.0
        if keys[K_UP] or keys[K_w]:
            control.throttle = 1.0
        if keys[K_DOWN] or keys[K_s]:
            control.brake = 1.0
        if keys[K_SPACE]:
            control.hand_brake = True
        if keys[K_q]:
            self._is_on_reverse = not self._is_on_reverse
        if keys[K_p]:
            self._autopilot_enabled = not self._autopilot_enabled
        control.reverse = self._is_on_reverse
        return control

    def _on_render(self):
        if self._surface is not None:
            self._display.blit(self._surface, (0, 0))
        pygame.display.flip()

    def _parse_image(self, image):
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        self._surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))

    def execute(self):
        pygame.init()
        try:
            self._display = pygame.display.set_mode(
                (WINDOW_WIDTH, WINDOW_HEIGHT),
                pygame.HWSURFACE | pygame.DOUBLEBUF)
            logging.debug('pygame started')

            world = self._client.get_world()
            blueprint = random.choice(
                world.get_blueprint_library().filter('vehicle'))
            self._vehicle = world.spawn_actor(blueprint, START_POSITION)
            self._vehicle.set_autopilot(self._autopilot_enabled)

            blueprint_library = world.get_blueprint_library()

            # Now let's filter all the blueprints of type 'vehicle' and
            # choose one at random.
            bp = random.choice(blueprint_library.filter('vehicle'))

            # A blueprint contains the list of attributes that define a vehicle
            # instance, we can read them and modify some of them. For instance,
            # let's randomize its color.
            color = random.choice(bp.get_attribute('color').recommended_values)
            bp.set_attribute('color', color)

            # So let's tell the world to spawn a vehicle. We can this NPC
            # because we are gonna let it run in auto-pilot
            self._npc_vehicle = world.spawn_actor(bp, NPC_START_POSITION)
            self._npc_vehicle.set_autopilot(True)

            # Let's add now a camera attached to the vehicle. Note that the
            # transform we give here is now relative to the vehicle.
            camera_bp = world.get_blueprint_library().find('sensor.camera')
            self._camera = world.spawn_actor(
                camera_bp, CAMERA_POSITION, attach_to=self._vehicle)
            print('created %s' % self._camera.type_id)

            self._camera.listen(lambda image: self._parse_image(image))
            # Use this to store frames locally - but comment out the above
            # .listen
            # self._camera.listen(save_to_disk)

            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                self._on_loop()
                self._on_render()
        finally:
            pygame.quit()
            if self._camera is not None:
                self._camera.destroy()
                self._camera = None
            if self._vehicle is not None:
                self._vehicle.destroy()
                self._vehicle = None
            if self._npc_vehicle is not None:
                self._npc_vehicle.destroy()
                self._npc_vehicle = None
            print('done.')


def main():
    argparser = argparse.ArgumentParser(
        description='CARLA Manual Control Client')
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='debug',
        help='print debug information')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='localhost',
        help='IP of the host server (default: localhost)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2001,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-a', '--autopilot',
        action='store_true',
        help='enable autopilot')
    args = argparser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.info('listening to server %s:%s', args.host, args.port)

    print(__doc__)

    while True:
        try:

            game = CarlaGame(args)
            game.execute()
            break

        except Exception as error:
            logging.error(error)
            time.sleep(1)


if __name__ == '__main__':

    main()
