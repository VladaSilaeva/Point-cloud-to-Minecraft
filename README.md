# Point-cloud-to-Minecraft
A simple tool to voxelize point cloud and add it to Minecraft

This project is based on nikitakrutoy's project [Points2Minecraft](https://github.com/nikitakrutoy/Points2Minecraft).

las2mc.py open .las files with laspy, voxelize point cloud with open3d and then add voxels to Minecraft map with amulet.

The map from colors to Minecraft block is done using idea from [here](https://projects.raspberrypi.org/en/projects/minecraft-selfies/5).

Tested on Minecraft 1.19. For the versions below, you need to create a new color map: a picture, each pixel of which is the average color of the texture of a certain block, and the python dictionary "pixel indexes in the picture": "block name" saved with pickle.

## Usage
```
python las2mc.py [OPTIONS]

  Turns point cloud into voxel grid and places voxel in Minecraft

Options:
  -f, --filename FILE          Path to .las point cloud
  -s, --scale FLOAT            A variable to scale points coords
  -v, --voxel FLOAT            How big are voxels gonna be
  -cm1 FILE                    Reference 6px-6px image for closest colors match.
  -cm2 FILE                    Map from colors to Minecraft block ids
  -mp DIRECTORY                Which map to modify
  -p, --postion FLOAT...       Where to build (x, z). If not specified, builds near spawn
  --help                       Show this message and exit.
```
On Windows you can find your Minecraft maps in %APPDATA%/.minecraft/saves
