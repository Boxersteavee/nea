from astropy.io import fits
from astropy.stats import sigma_clipped_stats
import twirl
import numpy
import matplotlib.pyplot as plt
from photutils.aperture import CircularAperture
from astropy.wcs import WCS

with fits.open('assets/input.fits') as image:
    data = image[0].data
    header = image[0].header
    try:
        true_wcs = WCS(header)
        print("WCS Data Found! Proceeding.")
    except:
        true_wcs = None
        print("No WCS data found. Proceeding without.")

mean, median, std = sigma_clipped_stats(data, sigma=3.0)
peaks = twirl.find_peaks(data, threshold=0)[0:20]
x_peaks = peaks[1]
y_peaks = peaks[0]
xy = list(zip(x_peaks, y_peaks))

if data.ndim == 3:
    plt.imshow(data[0, :, :], vmin=numpy.median(data), vmax=3 * numpy.median(data), cmap="Greys_r")
else:
    plt.imshow(data, vmin=numpy.median(data), vmax=3 * numpy.median(data), cmap="Greys_r")

_ = CircularAperture(xy, r=10.0).plot(color="y")

print(f"Number of peaks found: {len(xy)}")
plt.show()