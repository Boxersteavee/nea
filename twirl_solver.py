# This script is for using the twirl solving method.
# AstroPy Twirl plate-solves images using the ESA's GAIA online catalogue.

# Imports for find_stars()
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
import twirl
import numpy
import matplotlib.pyplot as plt
from photutils.aperture import CircularAperture
from astropy.wcs import WCS

# Imports for Twirl
from astropy.wcs.utils import proj_plane_pixel_scales
from twirl import gaia_radecs
from twirl.geometry import sparsify
from twirl import compute_wcs
from astropy.coordinates import SkyCoord


def find_stars(file):  # Function for identifying bright spots in the image (stars)
    with fits.open(file) as image:
        data = image[0].data  # Extract the image data into "data"
        header = image[0].header  # Extract the header of the image (which contains WCS data) into "header"
        try:
            true_wcs = WCS(header)
            print("WCS Data Found! Proceeding.")
        except:
            true_wcs = None
            print("No WCS data found. Proceeding.")

    mean, median, std = sigma_clipped_stats(data, sigma=3.0)
    xy = twirl.find_peaks(data)[0:20]

    if data.ndim == 3:
        plt.imshow(data[0, :, :], vmin=numpy.median(data), vmax=3 * numpy.median(data), cmap="Greys_r")
    else:
        plt.imshow(data, vmin=numpy.median(data), vmax=3 * numpy.median(data), cmap="Greys_r")

    xy_positions = [(x, y) for x, y, _ in xy]
    _ = CircularAperture(xy_positions, r=10.0).plot(color="y")

    print(f"Number of stars identified: {len(xy)}")
    plt.show()