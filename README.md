CARLA Simulator
===============

This repository contains a *modified* version of CARLA 0.9.0. The Python client provided in this repo can be used either with the provided Unreal project or a binary release of CARLA 0.9.0, which will be available here soon.


## Requirements
- `Python2.7`
- `cmake 3.9.0`

## Using the Unreal project

The following instructions assume CARLA will be built from source. Detailed instructions for CARLA are available [here](https://carla.readthedocs.io/en/stable/how_to_build_on_linux/).

1. Ensure Unreal 4.19 is installed and `UE4_ROOT` is set to the root of your Unreal 4.19 directory. At the moment you need to compile and build it from source.
```
# e.g.
export UE4_ROOT=~/UnrealEngine-4.19/
```
2. Run:
- `./Update.sh`, to download all CARLA content
3. make launch   # Compiles CARLA and launches Unreal Engine's Editor.
4. make package  # (Optional) Compiles CARLA and creates a packaged version for distribution.
5. make PythonAPI   # To be able to run python client code, but make sure you already ran the previous steps excluding 4.


## Useful commands
- Launching the editor
```
cd Unreal/CarlaUE4
~/UnrealEngine_4.19/Engine/Binaries/Linux/UE4Editor "$PWD/CarlaUE4.uproject"
```
- Compiling some changes without doing a full rebuild
```
cd Unreal/CarlaUE4
make CarlaUE4Editor
```

### Useful Scripts

These utility scripts are found in the `scripts` folder.

`load_carla_editor.bash`
- Loads the Carla editor project found `carla-pysim`. Use `-h` for help, and it
requires `UE4_ROOT` to be already set via `.bashrc`. To load another level
(aside from the default), put the level name as an argument, such as: `bahs
load_carla_editor.bash FlatEarth`

`python_dependencies_install.bash`
- Installs relevant python dependencies to ensure that the python client scripts
execute properly

`set_clang_X_X.bash`
- Modifies the binary symlinks to point to a specific clang version, denoted by
`X_X`. This assumes that that version for clang is already installed using
`apt-get`

## Using the packaged simulator
All the information below is discussed in the official CARLA docs. This is just an overview summary of some useful info.
When you run the client code, make sure the server is running.
Launch CARLA simulator server in standalone mode with default setting:
```
./CarlaUE4.sh
```

You could also launch with a set window size:
```
./CarlaUE4.sh -windowed -ResX=500 -ResY=500
```

Run client in manual control. The flag `-m` displays the live 2D map of cars moving.
```
cd PythonClient
python manual_control.py -m
```

You can modify and run the following script to send custom control commands:
```
python basic_path_demo.py
```

If you want to load a map, other than the default map, you can do so by running:
```
./CarlaUE4.sh /Game/Maps/Town02 -windowed -ResX=500 -ResY=500
```
Note: When specifying the map, make sure its the first argument, as there is no flag associated with it.

Now load the custom maps (for these make sure you are using the provided carla binaries as opposed to the official
carla binaries):
```
./CarlaUE4.sh /Game/Maps/BasicPlane -windowed -ResX=500 -ResY=500 -world-port=2001
```

```
./CarlaUE4.sh /Game/Maps/FlatEarth -windowed -ResX=500 -ResY=500 -world-port=2001
```

If you are using the custom maps above, before you run scripts such as `manual_control.py`, you may want to disable
the random spawning of non_player agents such as vehicles and pedestrian from inside `CarlaSettings()`.
```
settings = CarlaSettings()
settings.set(
    NumberOfVehicles=0,
    NumberOfPedestrians=0)
```
Otherwise you will get random agents getting dropped into the scene and crashing.

## [Keyboard Inputs](http://carla.readthedocs.io/en/latest/simulator_keyboard_input/)

Key             | Action
---------------:|:----------------
`W`             | Throttle
`S`             | Brake
`A` `D`         | Steer
`Q`             | Toggle reverse gear
`Space`         | Hand-brake
`P`             | Toggle autopilot
`←` `→` `↑` `↓` | Move camera
`PgUp` `PgDn`   | Zoom in and out
`Mouse Wheel`   | Zoom in and out
`Tab`           | Toggle on-board camera
`F11`           | Toggle fullscreen
`R`             | Restart level
`G`             | Toggle HUD
`C`             | Change weather/lighting
`Enter`         | Jump
`F`             | Use the force
`Alt+F4`        | Quit


## [Control commands](http://carla.readthedocs.io/en/latest/measurements/)
This is the structure used to send the vehicle control to the server.

Key                        | Type      | Description
-------------------------- | --------- | ------------
steer                      | float     | Steering angle between [-1.0, 1.0] (*)
throttle                   | float     | Throttle input between [ 0.0, 1.0]
brake                      | float     | Brake input between [ 0.0, 1.0]
hand_brake                 | bool      | Whether the hand-brake is engaged
reverse                    | bool      | Whether the vehicle is in reverse gear


## [Time-stamps](http://carla.readthedocs.io/en/latest/measurements/#time-stamps)

Key                        | Type      | Units        | Description
-------------------------- | --------- | ------------ | ------------
platform_timestamp         | uint32    | milliseconds | Time-stamp of the current frame, as given by the OS.
game_timestamp             | uint32    | milliseconds | In-game time-stamp, elapsed since the beginning of the current level.


## Debugging
- Error connecting to the server, even when the server is running. Since this is a TCP connection, it could fail sometimes due to
server timed-out, server is doing a reset etc. If this persists, you may just want to restart the server.

```
ERROR: (localhost:2000) failed to connect: [Errno 111] Connection refused
```

For this one, kill and re-run the client.
```
ERROR: (localhost:2000) failed to read data: timed out
```

In the case when these connection issues persist, try changing the port number.
1. On the server-side:
```
./CarlaUE4.sh -windowed -ResX=500 -ResY=500 -world-port=2001
```
2. On the client-side:
```
python client_example.py --port=2001
```


## Video Capture
The script `client_example.py` has an example for this. You need to add the following
code snippet:
```
# Iterate every frame in the episode.
for frame in range(0, frames_per_episode):

    # Read the data produced by the server this frame.
    measurement, sensor_data = client.read_data()

    for name, measurement in sensor_data.items():
        filename = args.out_filename_format.format(episode, name, frame)
        measurement.save_to_disk(filename)
```
This however makes the simulation very laggy. The frames are stored under `PythonClient/_out/`

## [Cameras and sensor](http://carla.readthedocs.io/en/latest/cameras_and_sensors/)
Four different sensors:
- Camera: Scene final
- Camera: Depth map
- Camera: Semantic segmentation
- Ray-cast based lidar


## [Map customization](http://carla.readthedocs.io/en/latest/map_customization/)
1. Follow the instructions on [How to build CARLA on Linux](http://carla.readthedocs.io/en/latest/how_to_build_on_linux/)
2. [Map customization](http://carla.readthedocs.io/en/latest/map_customization/)
3. Once you have generated maps using the editor, these maps should be under
```
UnrealEngine_4.19/carla/Unreal/CarlaUE4/Content/Maps
```
Next, go to the directory `UnrealEngine_4.19/carla/Unreal/CarlaUE4/Config`. Open the file `DefaultGame.ini` and add the maps
to cook:
```
+MapsToCook=(FilePath="/Game/Maps/MyAwesomeMap")
```
Note: This needs to be confirmed, but I think when you generate maps, to be able to run demos such as `manual_control.py`,
need to keep `PlayerStarts` assets which can be copied over from the DefaultMap.

4. With all the maps in place, now you need to create a binary version of CARLA.
The recommended way is to use the `Package.sh` script provided. Alternatively, open the CarlaUE4 project via Unreal,
go to the menu `File -> Package Project`, and select your platform, linux in this case.
Before you run the `Package.sh` make sure `UE4_ROOT` is in the environment as it looks at the
environment variable `UE4_ROOT` to find the right version of Unreal Engine.
```
export UE4_ROOT=~/UnrealEngine_4.19
```

5. If all the above steps go well, you should have the packaged binaries under the directory:
```
UnrealEngine_4.19/carla/Dist/0.9.0-24-xxxxx/LinuxNoEditor
```
