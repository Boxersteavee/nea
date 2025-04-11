from astropy.io import fits
from astropy.stats import sigma_clipped_stats
import twirl
import numpy
import matplotlib.pyplot as plt
from photutils.aperture import CircularAperture
from astropy.wcs import WCS

def find_stars(file): # Function for finding stars
    with fits.open(file) as image: # Open input file (input.fits)
        data = image[0].data # Save the image data (picture) in 'data'
        header = image[0].header # Save the image header (WCS data) in 'header'
        try:
            true_wcs = WCS(header) # Save WCS data in 'true_wcs' for later.
            print("WCS Data Found! Proceeding.")
        except:
            true_wcs = None # If the image does not have WCS data, proceed without it.
            print("No WCS data found. Proceeding without.")

    xy = twirl.find_peaks(data)[0:50]

    if xy.shape[1] == 3:
        xy_positions = [(x, y) for x, y, _ in xy]
    else:
        xy_positions = [(x, y) for x, y in xy]

    plt.figure(figsize=(6.4, 3.6), dpi=300) # Set image resolution to 300dpi

    if data.ndim == 3:
        plt.imshow(data[0, :, :], vmin=numpy.median(data), vmax=3 * numpy.median(data), cmap="Greys_r")
    else:
        plt.imshow(data, vmin=numpy.median(data), vmax=3 * numpy.median(data), cmap="Greys_r")

    _ = CircularAperture(xy_positions, r=40.0).plot(color="y")

    print(f"Number of stars found: {len(xy)}")
    plt.show()