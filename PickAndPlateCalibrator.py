import cv2
import Tkinter as tk
import tkFileDialog as filedialog
from time import time, sleep
import numpy as np
import os
import math

RESIZE_SIZE = (480, 270)

CROP_X_CENTER = 961
CROP_Y_CENTER = 583
CROP_DIM = 545
CROP_DIM_HALF = CROP_DIM / 2

RED = (0, 0, 255)
GREEN = (0, 255, 0)

WELL_WALL_LINE_THICKNESS = 1

WELL_CENTER_RADIUS = 1
WELL_CENTER_LINE_THICKNESS = -1  # -1 is filled in circle

master = tk.Tk()
images = []


def perform_detection(_):
    global images

    # minimum_distance = min_dist.get()
    minimum_size = min_size.get()
    maximum_size = max_size.get()
    usable_area_offset = area_offset.get()

    for current_image in images:
        x1 = CROP_X_CENTER - CROP_DIM_HALF
        x2 = CROP_X_CENTER + CROP_DIM_HALF
        y1 = CROP_Y_CENTER - CROP_DIM_HALF
        y2 = CROP_Y_CENTER + CROP_DIM_HALF

        gray = cv2.cvtColor(current_image[1].copy(), cv2.COLOR_BGR2GRAY)

        mask_frame = gray.copy()
        mask_frame.fill(0)

        cv2.circle(mask_frame, (CROP_X_CENTER, CROP_Y_CENTER), (CROP_DIM_HALF - usable_area_offset), 255, -1)  # Fill the mask with 1's for a circle where the dish is in the image

        orig_now_masked = cv2.bitwise_and(gray, mask_frame)

        image_bgr = cv2.cvtColor(orig_now_masked, cv2.COLOR_GRAY2BGR)[y1: y2, x1:x2]
        image_bgr_orig = image_bgr.copy()
        image_name = os.path.split(current_image[0])[-1]
##############################################################
        imgray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        # im_gauss = cv2.GaussianBlur(imgray, (5, 5), 0)
        ret, thresh = cv2.threshold(imgray, 127, 255, 0)
        # get contours
        im2, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        contours_area = []
        # calculate area and filter into new array
        for con in contours:
            area = cv2.contourArea(con)
            if 0 < area < max_size:
                contours_area.append(con)

        contours_cirles = []

        # check if contour is of circular shape
        for con in contours_area:
            perimeter = cv2.arcLength(con, True)
            if perimeter == 0:
                break

            if perimeter < 100:
                contours_cirles.append(con)

        pickable_embryos = []

        for current_contour in contours_cirles:
            current_embryo_area = cv2.contourArea(current_contour)
            current_embryo_diameter = np.sqrt(4 * current_embryo_area / np.pi)

            current_embryo_movement = cv2.moments(current_contour)
            current_embryo_x = int(current_embryo_movement["m10"] / current_embryo_movement["m00"])
            current_embryo_y = int(current_embryo_movement["m01"] / current_embryo_movement["m00"])

            found_too_close = False

            for other_contour in contours_cirles:
                other_embryo_area = cv2.contourArea(other_contour)
                other_embryo_diameter = np.sqrt(4 * other_embryo_area / np.pi)

                other_embryo_movement = cv2.moments(other_contour)
                other_embryo_x = int(other_embryo_movement["m10"] / other_embryo_movement["m00"])
                other_embryo_y = int(other_embryo_movement["m01"] / other_embryo_movement["m00"])

                if (other_embryo_x == current_embryo_x) and (other_embryo_y == current_embryo_y):
                    pass
                elif (math.sqrt(pow(abs(other_embryo_x - current_embryo_x), 2) + pow(abs(other_embryo_y - current_embryo_y), 2)) - (other_embryo_diameter / 2) - (current_embryo_diameter / 2)) < min_dist_between.get():
                    found_too_close = True
                    break

            if not found_too_close:
                perimeter = cv2.arcLength(current_contour, True)
                if perimeter == 0:
                    break

                circularity = 4 * math.pi * (current_embryo_area / (perimeter * perimeter))

                if min_circ.get() < circularity < 1.0 and current_embryo_area > min_size.get():
                    pickable_embryos.append(current_contour)

        cv2.drawContours(image_bgr, contours_cirles, -1, (0, 0, 255), 2)
        cv2.drawContours(image_bgr, pickable_embryos, -1, (0, 255, ), 2)


###############################################################
        # blurred = cv2.medianBlur(image_bgr, 3)
        # image_gray = cv2.cvtColor(blurred, cv2.COLOR_RGB2GRAY)
        #
        # wells = cv2.HoughCircles(image_gray, cv2.HOUGH_GRADIENT, 1, minimum_distance,
        #                          param1=12, param2=87,
        #                          minRadius=minimum_size, maxRadius=maximum_size)
        #
        # if wells is not None:
        #     wells = np.uint16(np.around(wells))[0, :]
        #
        #     # Convert to python list for easier manipulation
        #     wells = [list(item) for item in wells]
        #     print len(wells)
        #
        #     for i in wells:
        #         # draw the outer well
        #         cv2.circle(image_bgr, (i[0], i[1]), i[2], GREEN, WELL_WALL_LINE_THICKNESS)
        #
        #         # draw the center of the well
        #         cv2.circle(image_bgr, (i[0], i[1]), WELL_CENTER_RADIUS, RED, WELL_CENTER_LINE_THICKNESS)
##################################################################
        cv2.imshow(image_name + " detected", image_bgr)
        cv2.imshow(image_name + " orig", image_bgr_orig)
        print "Displayed"


if __name__ == '__main__':
    area_offset = tk.Scale(master, from_=1, to=255, orient=tk.HORIZONTAL, label="Usable Area Offset")
    area_offset.set(65)
    area_offset.bind("<ButtonRelease-1>", perform_detection)
    area_offset.pack(fill="both", expand=True)

    min_size = tk.Scale(master, from_=0, to=1000, orient=tk.HORIZONTAL, label="Min Size")
    min_size.set(5)
    min_size.bind("<ButtonRelease-1>", perform_detection)
    min_size.pack(fill="both", expand=True)

    max_size = tk.Scale(master, from_=1, to=10000, orient=tk.HORIZONTAL, label="Max Size")
    max_size.set(51)
    max_size.bind("<ButtonRelease-1>", perform_detection)
    max_size.pack(fill="both", expand=True)

    min_circ = tk.Scale(master, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL, label="Min Circularity")
    min_circ.set(0.75)
    min_circ.bind("<ButtonRelease-1>", perform_detection)
    min_circ.pack(fill="both", expand=True)

    min_dist_between = tk.Scale(master, from_=0, to=20, resolution=0.1, orient=tk.HORIZONTAL, label="Min Distance Between")
    min_dist_between.set(6)
    min_dist_between.bind("<ButtonRelease-1>", perform_detection)
    min_dist_between.pack(fill="both", expand=True)

    files = filedialog.askopenfilenames(title="Image Files")
    for filename in files:
        images.append((filename, cv2.imread(filename)))

    perform_detection(None)

    master.mainloop()
