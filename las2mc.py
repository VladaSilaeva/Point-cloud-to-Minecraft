import pickle
import click
import numpy as np
import laspy
import open3d as o3d
from skimage import io, color
import amulet
from amulet.api.block import Block
from amulet.utils.world_utils import block_coords_to_chunk_coords
from amulet.api.selection import SelectionBox


@click.command()
@click.option('-f', '--filename', 'filename', type=click.Path(exists=True, dir_okay=False),
              help="Path to .las point cloud")
@click.option('-s', '--scale', 'scale', default=1, type=float,
              help="A variable to scale points coords")
@click.option('-v', '--voxel', 'voxel_size', default=1.0, type=float,
              help="How big are voxels gonna be")
@click.option('-cm1', 'color_map_png', type=click.Path(exists=True, dir_okay=False, file_okay=True),
              help="Reference 6px-6px image for closest colors match.")
@click.option('-cm2', 'color_map_pkl', type=click.Path(exists=True, dir_okay=False, file_okay=True),
              help="Map from colors to Minecraft block ids")
@click.option('-mp', 'map_path', type=click.Path(exists=True, dir_okay=True, file_okay=False),
              help="Which map to modify")
@click.option("-p", "--position", type=int, nargs=2, default=None,
              help="Where to build (x, z). If not specified, builds near 0 60 0")



def voxelize(filename, scale, voxel_size, color_map_png, color_map_pkl, map_path, position,):
    if not position: position = np.array((0, 60, 0))
    else: position = np.array((position[0], 60, position[1]))
    
    point_cloud = laspy.read(filename)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(np.vstack((point_cloud.x, point_cloud.z, point_cloud.y)).transpose() / scale)
    pcd.colors = o3d.utility.Vector3dVector(np.vstack((point_cloud.red, point_cloud.green, point_cloud.blue)).transpose()/65535)
    voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(pcd, voxel_size=voxel_size)
    
    box_size = np.array(((voxel_grid.get_max_bound() - voxel_grid.get_min_bound()) / voxel_size).astype(int))
    box_size[1], box_size[2] = box_size[2], box_size[1]
    indeces = np.array(list(v.grid_index[[0, 2, 1]] for v in voxel_grid.get_voxels()))
    colors = np.array(list(v.color for v in voxel_grid.get_voxels()))
    
    add2mc(color_map_png, color_map_pkl, map_path, position, box_size, indeces, colors)

def add2mc(color_map_png, color_map_pkl, map_path, position, box_size, indeces, colors):
    map_rgb = io.imread(color_map_png)
    map_lab = color.rgb2lab(map_rgb)
    with open(color_map_pkl, "rb") as f:
        color_map_name = pickle.load(f)
    
    # загрузка мира
    level = amulet.load_level(map_path)
    
    # загрузка палитры блоков
    color_map_id = dict()
    for pixel, name in color_map_name.items():
        block = Block("minecraft", name, {},)
        (universal_block, universal_block_entity, universal_extra,) = level.translation_manager.get_version("java", (1, 19, 0)).block.to_universal(block)
        block_id = level.block_palette.get_add_block(universal_block)
        color_map_id[pixel] = block_id
    def color2block(c):
        distance = 1000
        voxel_color = color.rgb2lab([[c]])[0][0]
        for k, map_column in enumerate(map_lab):
            for l, map_pixel in enumerate(map_column):
                delta = color.deltaE_cie76(voxel_color, map_pixel)
                if delta < distance:
                    distance = delta
                    block_id = color_map_id[(k, l)]
        return block_id
    
    # очистка пространства от блоков
    block = Block("minecraft", "air", {},)
    (universal_block, universal_block_entity, universal_extra,) = level.translation_manager.get_version("java", (1, 19, 0)).block.to_universal(block)
    air_id = level.block_palette.get_add_block(universal_block)    
    box = SelectionBox(position, np.sum([position, box_size], axis=0))
    for (cx, cz), subbox in box.chunk_boxes():
        chunk = level.get_chunk(cx, cz, "minecraft:overworld")
        chunk.changed = True
        for x, y, z in subbox:
            chunk.blocks[x - 16*cx, y,  z - 16*cz] = air_id
    
    # перевод вокселей в блоки и строительство блоков
    for position2, c in zip(indeces, colors):
        x, y, z = np.sum([position, position2], axis=0)
        cx, cz = block_coords_to_chunk_coords(x, z)
        chunk = level.get_chunk(cx, cz, "minecraft:overworld")
        chunk.blocks[x - 16*cx, y, z - 16*cz] = color2block(c)
        chunk.changed = True
    # сохранение мира
    level.save()
    level.close()    

def main():
    voxelize()

if __name__ == "__main__":
    voxelize()
