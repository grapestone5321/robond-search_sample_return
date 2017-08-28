import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select


def color_thresh_obstacle(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select1 = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # bellow_eq_thresh will now contain a boolean array with "True"
    # where threshold was met
    bellow_eq_thresh = (img[:,:,0] <= rgb_thresh[0]) \
                & (img[:,:,1] <= rgb_thresh[1]) \
                & (img[:,:,2] <= rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select1[bellow_eq_thresh] = 1
    # Return the binary image
    return color_select1


def color_thresh_rock(img, rgb_low=(100, 100, 0), rgb_high=(230, 230, 80)):
    # Create an array of zeros same xy size as img, but single channel
    color_select2 = np.zeros_like(img[:,:,0])
    # Require that each pixel be between threshold values in RGB
    #  in_range will now contain a boolean array with "True"
    # where threshold was met
    in_range = ((img[:,:,0] >= rgb_low[0]) & (img[:,:,0] <= rgb_high[0])) \
                & ((img[:,:,1] >= rgb_low[1]) & (img[:,:,1] <= rgb_high[1])) \
                & ((img[:,:,2] >= rgb_low[2]) & (img[:,:,2] <= rgb_high[2]))
    # Index the array of zeros with the boolean array and set to 1
    color_select2[in_range] = 1
    # Return the binary image
    return color_select2


# Define a function to convert from image coords to rover coords
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = -(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[1]/2 ).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to map rover space pixels to world space
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))
                            
    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result  
    return xpix_rotated, ypix_rotated

def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale): 
    # Apply a scaling and a translation
    
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result  
    return xpix_translated, ypix_translated


# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image

    #mask = cv2.warpPerspective(np.ones_like(img[:,:,0]), M, (img.shape[1], img.shape[0]))
    
    return warped


# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # TODO:
    # NOTE: camera image is coming to you in Rover.img
    image = Rover.img
    # 1) Define source and destination points for perspective transform
    dst_size = 5
    bottom_offset = 6
    source = np.float32([[14, 140], [301 ,140],[200, 96], [118, 96]])
    destination = np.float32([[image.shape[1]/2 - dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - 2*dst_size - bottom_offset],
                  [image.shape[1]/2 - dst_size, image.shape[0] - 2*dst_size - bottom_offset],
                  ])


    # 2) Apply perspective transform
    warped = perspect_transform(image, source, destination)

    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    threshed_terrain = color_thresh(warped)
    print('threshed_terrain=' + str(threshed_terrain))
    threshed_obstacle = color_thresh_obstacle(warped)
    print('threshed_obstacle' + str(threshed_obstacle))
    threshed_rockimage = color_thresh_rock(warped)
    print('color_thresh_rock' + str(threshed_rockimage))

    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
        # Example: Rover.vision_image[:,:,0] = obstacle color-thresholded binary image
        #          Rover.vision_image[:,:,1] = rock_sample color-thresholded binary image
        #          Rover.vision_image[:,:,2] = navigable terrain color-thresholded binary image
    Rover.vision_image[:,:,0] = threshed_obstacle  * 255
    Rover.vision_image[:,:,1] = threshed_rockimage  * 255
    Rover.vision_image[:,:,2] = threshed_terrain * 255

    # 5) Convert map image pixel values to rover-centric coords
    xpix_terrain, ypix_terrain = rover_coords(threshed_terrain)
    xpix_obstacle, ypix_obstacle = rover_coords(threshed_obstacle)
    xpix_rockimage, ypix_rockimage = rover_coords(threshed_rockimage)

    # 6) Convert rover-centric pixel values to world coordinates
    (rover_xpos, rover_ypos) = Rover.pos
    rover_yaw = Rover.yaw
    rover_roll = Rover.roll
    rover_pitch = Rover.pitch
    worldsize = Rover.worldmap.shape[0]
    worldmap = np.zeros((200, 200))
    scale = dst_size * 2
    x_world_terrain, y_world_terrain = pix_to_world(xpix_terrain, ypix_terrain, rover_xpos,
                                       rover_ypos, rover_yaw, worldsize, scale)

    x_world_obstacle, y_world_obstacle = pix_to_world(xpix_obstacle, ypix_obstacle, rover_xpos,
                                       rover_ypos, rover_yaw, worldsize, scale)

    x_world_rockimage, y_world_rockimage = pix_to_world(xpix_rockimage, ypix_rockimage, rover_xpos,
                                       rover_ypos, rover_yaw, worldsize, scale)

    print ('x_world_rockimage=' + str(x_world_rockimage) + ' y_world_rockimage=' + str(y_world_rockimage) )

    # 7) Update Rover worldmap (to be displayed on right side of screen)
    if ((rover_roll <= 0.5) or (rover_roll >= 300)):
        if rover_pitch <= 0.5 or rover_pitch >= 300:
            Rover.worldmap[y_world_obstacle, x_world_obstacle, 0] += 255
            Rover.worldmap[y_world_rockimage, x_world_rockimage, 1] += 255
            Rover.worldmap[y_world_terrain, x_world_terrain, 2] += 255

    # 8) Convert rover-centric pixel positions to polar coordinates
    # Update Rover pixel distances and angles
        # Rover.nav_dists = rover_centric_pixel_distances
        # Rover.nav_angles = rover_centric_angles

    Rover.rock_dists , Rover.rock_angles = to_polar_coords(xpix_rockimage, ypix_rockimage)
    Rover.nav_dists, Rover.nav_angles = to_polar_coords(xpix_terrain, ypix_terrain)


    return Rover
