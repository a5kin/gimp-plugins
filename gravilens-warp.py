#!/usr/bin/env python
import math

import gimpfu as fu
from array import array


def gravilens_warp(img, layer, inner_radius_percent,
                   outer_radius_percent, inside):
    """
    Create gravitational lens effect over selected region.

    :param img:
        The current image.
    :param layer:
        The layer of the image that is selected.
    :param inner_radius_percent:
        Inner radius of the lens in percents.
    :param outer_radius_percent:
        Outer radius of the lens in percents.
    :param inside:
        False - values insine inner raduis are black,
        True - reflected neighbourhood inside inner radius.

    """
    # prepare warp
    fu.gimp.progress_init("Warping space...")
    fu.pdb.gimp_image_undo_group_start(img)

    # get selection
    is_selection, x1, y1, x2, y2 = fu.pdb.gimp_selection_bounds(img)
    if not is_selection:
        x1, y1, x2, y2 = 0, 0, img.width, img.height

    # create temp layer
    layer_pos = img.layers.index(layer)
    new_layer = fu.gimp.Layer(img, layer.name + " temp", layer.width,
                              layer.height, layer.type, layer.opacity,
                              layer.mode)
    img.add_layer(new_layer, layer_pos)
    layer_name = layer.name
    fu.pdb.gimp_edit_clear(new_layer)
    new_layer.flush()

    # calculate constants
    max_radius = min(x2 - x1, y2 - y1) / 2.
    inner_radius = max_radius * inner_radius_percent / 100.
    outer_radius = max_radius * outer_radius_percent / 100.
    x_center = (x2 + x1) / 2.
    y_center = (y2 + y1) / 2.

    # prepare pixel arrays
    src_rgn = layer.get_pixel_rgn(0, 0, layer.width, layer.height,
                                  False, False)
    dst_rgn = new_layer.get_pixel_rgn(0, 0, layer.width, layer.height,
                                      True, False)
    pixel_size = len(src_rgn[0, 0])
    src_array = array("B", src_rgn[0:layer.width, 0:layer.height])
    dst_array = array("B", src_rgn[0:layer.width, 0:layer.height])

    # process pixel array
    for x in range(layer.width):
        fu.gimp.progress_update(float(x) / float(layer.width))
        if x < x1 or x >= x2:
            continue
        for y in range(layer.height):
            if y < y1 or y >= y2:
                continue
            # calculate warp position
            dx, dy = x - x_center, y - y_center
            r = math.hypot(dx, dy)
            denom = (outer_radius - inner_radius) or 1
            ratio = min(1, (r - inner_radius) / denom)
            # ratio = (r - inner_radius) / denom
            if ratio > 0:
                ratio = 1 - (1 - ratio) ** 2
                if ratio > 0:
                    ratio = math.sqrt(ratio)
                else:
                    ratio = -math.sqrt(abs(ratio))
            x_warp = int(round(((dx * ratio + x_center) % layer.width)))
            y_warp = int(round(((dy * ratio + y_center) % layer.height)))
            # get pixel at warp position and put it to destination
            pos_orig = (y * layer.width + x) * pixel_size
            pos_warp = (y_warp * layer.width + x_warp) * pixel_size
            for i in range(pixel_size):
                val = src_array[pos_warp + i] if ratio >= 0 or inside else 0
                dst_array[pos_orig + i] = val

    # copy result to the image
    dst_rgn[0:layer.width, 0:layer.height] = dst_array.tostring()
    new_layer.flush()
    new_layer.merge_shadow(True)
    new_layer.update(0, 0, new_layer.width, new_layer.height)
    img.remove_layer(layer)
    new_layer.name = layer_name

    # finish warp
    fu.pdb.gimp_image_undo_group_end(img)
    fu.pdb.gimp_progress_end()


fu.register(
    "python_fu_gravilens_warp",
    "Gravitational Lens Warp",
    "Create gravitational lens effect over selected region.",
    "Andrey Zamaraev",
    "MIT License",
    "2018",
    "<Image>/Filters/Distorts/Gravitational Lens Warp",
    "GRAY*, RGB*",
    [
        (
            fu.PF_SLIDER,
            "inner_radius_percent", "Inner Radius, %",
            50, (0, 100, 0.1)
        ),
        (
            fu.PF_SLIDER,
            "outer_radius_percent", "Outer Radius, %",
            100, (0, 100, 0.1)
        ),
        (
            fu.PF_BOOL,
            "inside", "Render inside inner radius",
            False
        ),
    ],
    [],
    gravilens_warp
)

fu.main()
