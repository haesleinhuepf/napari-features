import collections.abc
import functools
import inspect
import math

import numpy
import scipy.ndimage
import scipy.stats
import skimage.measure
import skimage.morphology
import skimage.segmentation
import skimage.measure


def cache(wrapped):
    @functools.wraps(wrapped)
    def function(generator: "Generator"):
        name = wrapped.__name__

        if not (name in generator.cache):
            generator.cache[name] = wrapped(generator)

        return generator.cache[name]

    return function


class Generator(collections.abc.Iterator):
    def __init__(self, label, image):
        self.cache = {}

        self.image = skimage.img_as_float32(image)

        self.label = label

        self.multichannel = label.shape < image.shape

        self.objects = scipy.ndimage.find_objects(label)

        self.object_index = 1  # skip background (`0`)

        self.object = self.objects[self.object_index - 1]

        self.volumetric = False

        self._cropped = None

        self._spatial_axes = tuple(range(label.ndim))

    def __iter__(self):
        return self

    def __next__(self):
        try:
            self.object = self.objects[self.object_index - 1]
        except IndexError:
            raise StopIteration

        self.object_index = self.object_index + 1

        return [getattr(self, member) for member in self._members]

    @property
    @cache
    def area(self):
        return numpy.sum(self.label)

    @property
    @cache
    def central_moments(self):
        return skimage.measure.moments_central(self.label.astype(numpy.uint8), self.local_centroid, order=3)

    @property
    @cache
    def centroid(self):
        return self.coordinates.mean(axis=0)

    @property
    def columns(self):
        return [member.replace("_feature_", "") for member in self._members]

    @property
    @cache
    def convex_hull(self):
        return skimage.morphology.convex_hull_image(self.mask)

    @property
    @cache
    def coordinates(self):
        indices = numpy.nonzero(self.image)

        stack = []

        for index in range(self.label.ndim):
            stack += [indices[index] + self.object[index].start]

        return numpy.vstack(stack).T

    @property
    @cache
    def crop(self):
        return self.image[self.object]

    @property
    @cache
    def edge(self):
        boundary = skimage.segmentation.find_boundaries(self.mask, mode="outer")

        return self.crop * boundary

    @property
    @cache
    def inertia_tensor(self):
        return skimage.measure.inertia_tensor(self.image, self.central_moments)

    @property
    @cache
    def inertia_tensor_eigenvalues(self):
        return skimage.measure.inertia_tensor_eigvals(self.label, T=self.inertia_tensor)

    @property
    @cache
    def local_centroid(self):
        spatial_moments = self.spatial_moments

        return tuple(spatial_moments[tuple(numpy.eye(self.label.ndim, dtype=int))] / spatial_moments[(0,) * self.label.ndim])

    @property
    @cache
    def mask(self):
        return numpy.squeeze(self.label[self.object]) > 0

    @property
    @cache
    def masked(self):
        return self.image[self.object] * self.mask

    @property
    @cache
    def spatial_moments(self):
        m = skimage.measure.moments(skimage.img_as_ubyte(self.masked), 3)

        if not self.volumetric:
            v = numpy.zeros((4, 4, 4))

            v[0] = m

            return v

        return m

    # General-purpose features

    # Color

    # Color: Image

    @property
    def _feature_color_image_integrated_intensity(self):
        return numpy.sum(self.image)

    @property
    def _feature_color_image_maximum_intensity(self):
        return numpy.max(self.image)

    @property
    def _feature_color_image_mean_intensity(self):
        return numpy.mean(self.image)

    @property
    def _feature_color_image_median_absolute_deviation_intensity(self):
        return scipy.stats.median_absolute_deviation(self.image.reshape(-1, ))

    @property
    def _feature_color_image_median_intensity(self):
        return numpy.median(self.image)

    @property
    def _feature_color_image_minimum_intensity(self):
        return numpy.min(self.image)

    @property
    def _feature_color_image_quantile_1_intensity(self):
        return numpy.quantile(self.image, 0.25)

    @property
    def _feature_color_image_quantile_3_intensity(self):
        return numpy.quantile(self.image, 0.75)

    @property
    def _feature_color_image_standard_deviation_intensity(self):
        return numpy.std(self.image)

    # Color: Object

    @property
    def _feature_color_object_edge_integrated_intensity(self):
        return numpy.sum(self.edge)

    @property
    def _feature_color_object_edge_maximum_intensity(self):
        return numpy.max(self.edge)

    @property
    def _feature_color_object_edge_mean_intensity(self):
        return numpy.mean(self.edge)

    @property
    def _feature_color_object_edge_median_intensity(self):
        return numpy.median(self.edge)

    @property
    def _feature_color_object_edge_minimum_intensity(self):
        return numpy.min(self.edge)

    @property
    def _feature_color_object_edge_quantile_1_intensity(self):
        return numpy.quantile(self.edge, 0.25)

    @property
    def _feature_color_object_edge_quantile_3_intensity(self):
        return numpy.quantile(self.edge, 0.75)

    @property
    def _feature_color_object_edge_standard_deviation_intensity(self):
        return numpy.std(self.edge)

    @property
    def _feature_color_object_center_mass_intensity_x(self):
        return 0.0

    @property
    def _feature_color_object_center_mass_intensity_y(self):
        return 0.0

    @property
    def _feature_color_object_integrated_intensity(self):
        return numpy.sum(self.masked)

    @property
    def _feature_color_object_mass_displacement(self):
        return 0.0

    @property
    @cache
    def _feature_color_object_maximum_intensity(self):
        return numpy.max(self.masked)

    @property
    def _feature_color_object_maximum_intensity_x(self):
        xs, _ = numpy.where(self.image == self._feature_color_object_maximum_intensity)

        # If there are multiple matches, first match is returned.
        return xs[0]

    @property
    def _feature_color_object_maximum_intensity_y(self):
        _, ys = numpy.where(self.image == self._feature_color_object_maximum_intensity)

        # If there are multiple matches, first match is returned.
        return ys[0]

    @property
    def _feature_color_object_mean_intensity(self):
        return numpy.mean(self.masked)

    @property
    def _feature_color_object_median_absolute_deviation_intensity(self):
        return scipy.stats.median_absolute_deviation(self.masked.reshape(-1, ))

    @property
    def _feature_color_object_median_intensity(self):
        return numpy.median(self.masked)

    @property
    def _feature_color_object_minimum_intensity(self):
        return numpy.min(self.masked)

    @property
    def _feature_color_object_quantile_1_intensity(self):
        return numpy.quantile(self.masked, 0.25)

    @property
    def _feature_color_object_quantile_3_intensity(self):
        return numpy.quantile(self.masked, 0.75)

    @property
    def _feature_color_object_standard_deviation_intensity(self):
        return numpy.std(self.masked)

    # Location

    # Location: Object neighborhood

    @property
    def _feature_location_object_neighborhood_angle(self):
        return 0.0

    @property
    def _feature_location_object_neighborhood_closest_0_distance(self):
        return 0.0

    @property
    def _feature_location_object_neighborhood_closest_0_object_index(self):
        return 0.0

    @property
    def _feature_location_object_neighborhood_closest_1_distance(self):
        return 0.0

    @property
    def _feature_location_object_neighborhood_closest_1_object_index(self):
        return 0.0

    @property
    def _feature_location_object_neighborhood_closest_2_distance(self):
        return 0.0

    @property
    def _feature_location_object_neighborhood_closest_2_object_index(self):
        return 0.0

    @property
    def _feature_location_object_neighborhood_neighbors(self):
        return 0.0

    @property
    def _feature_location_object_neighborhood_touching(self):
        return 0.0

    # Metadata

    # Metadata: Image

    @property
    def _feature_metadata_image_checksum(self):
        return 0.0

    @property
    def _feature_metadata_image_filename(self):
        return 0.0

    # Metadata: Layer

    @property
    def _feature_metadata_layer_name(self):
        return 0.0

    @property
    def _feature_metadata_layer_type(self):
        return 0.0

    # Metadata: Object

    @property
    def _feature_metadata_object_index(self):
        return self.object_index

    # Shape

    # Shape: Image

    @property
    def _feature_shape_image_area(self):
        if self.multichannel:
            return numpy.product(numpy.product(self.image.shape[:-1]))
        else:
            return numpy.product(numpy.product(self.image.shape))

    # Shape: Image skeleton

    @property
    def _feature_shape_image_skeleton_branches(self):
        return 0.0

    @property
    def _feature_shape_image_skeleton_endpoints(self):
        return 0.0

    @property
    def _feature_shape_image_skeleton_length(self):
        return 0.0

    @property
    def _feature_shape_image_skeleton_trunks(self):
        return 0.0

    # Shape: Object

    @property
    def _feature_shape_object_area(self):
        return 0.0

    @property
    def _feature_shape_object_bounding_box_area(self):
        return 0.0

    @property
    def _feature_shape_object_bounding_box_maximum_x(self):
        return 0.0

    @property
    def _feature_shape_object_bounding_box_maximum_y(self):
        return 0.0

    @property
    def _feature_shape_object_bounding_box_maximum_z(self):
        return 0.0

    @property
    def _feature_shape_object_bounding_box_minimum_x(self):
        return 0.0

    @property
    def _feature_shape_object_bounding_box_minimum_y(self):
        return 0.0

    @property
    def _feature_shape_object_bounding_box_minimum_z(self):
        return 0.0

    @property
    def _feature_shape_object_bounding_box_volume(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_0_0_0(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_0_0_1(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_0_1_2(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_0_1_3(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_1_2_0(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_1_2_1(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_1_3_2(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_1_3_3(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_2_0_0(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_2_0_1(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_2_1_2(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_2_1_3(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_3_2_0(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_3_2_1(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_3_3_2(self):
        return 0.0

    @property
    def _feature_shape_object_central_moment_3_3_3(self):
        return 0.0

    @property
    def _feature_shape_object_centroid_x(self):
        return self.centroid[0]

    @property
    def _feature_shape_object_centroid_y(self):
        return self.centroid[1]

    @property
    def _feature_shape_object_centroid_z(self):
        return 0.0

    @property
    def _feature_shape_object_compactness(self):
        return 0.0

    @property
    def _feature_shape_object_eccentricity(self):
        return 0.0

    @property
    def _feature_shape_object_equivalent_diameter(self):
        return (2 * self.label.ndim * self.area / math.pi) ** (1 / self.label.ndim)

    @property
    def _feature_shape_object_euler_number(self):
        return skimage.measure.euler_number(self.label, self.label.ndim)

    @property
    def _feature_shape_object_extent(self):
        return self.area / self.label.size

    @property
    def _feature_shape_object_form_factor(self):
        return 0.0

    @property
    def _feature_shape_object_hu_moment_0(self):
        return 0.0

    @property
    def _feature_shape_object_hu_moment_1(self):
        return 0.0

    @property
    def _feature_shape_object_hu_moment_2(self):
        return 0.0

    @property
    def _feature_shape_object_hu_moment_3(self):
        return 0.0

    @property
    def _feature_shape_object_hu_moment_4(self):
        return 0.0

    @property
    def _feature_shape_object_hu_moment_5(self):
        return 0.0

    @property
    def _feature_shape_object_hu_moment_6(self):
        return 0.0

    @property
    def _feature_shape_object_inertia_tensor_eigenvalues_x(self):
        return 0.0

    @property
    def _feature_shape_object_inertia_tensor_eigenvalues_y(self):
        return 0.0

    @property
    def _feature_shape_object_inertia_tensor_eigenvalues_z(self):
        return 0.0

    @property
    def _feature_shape_object_inertia_tensor_x_x(self):
        return 0.0

    @property
    def _feature_shape_object_inertia_tensor_x_y(self):
        return 0.0

    @property
    def _feature_shape_object_inertia_tensor_x_z(self):
        return 0.0

    @property
    def _feature_shape_object_inertia_tensor_y_x(self):
        return 0.0

    @property
    def _feature_shape_object_inertia_tensor_y_y(self):
        return 0.0

    @property
    def _feature_shape_object_inertia_tensor_y_z(self):
        return 0.0

    @property
    def _feature_shape_object_inertia_tensor_z_x(self):
        return 0.0

    @property
    def _feature_shape_object_inertia_tensor_z_y(self):
        return 0.0

    @property
    def _feature_shape_object_inertia_tensor_z_z(self):
        return 0.0

    @property
    def _feature_shape_object_major_axis_length(self):
        return 0.0

    @property
    def _feature_shape_object_maximum_feret_diameter(self):
        return 0.0

    @property
    def _feature_shape_object_maximum_radius(self):
        return 0.0

    @property
    def _feature_shape_object_mean_radius(self):
        return 0.0

    @property
    def _feature_shape_object_median_radius(self):
        return 0.0

    @property
    def _feature_shape_object_minimum_feret_diameter(self):
        return 0.0

    @property
    def _feature_shape_object_minor_axis_length(self):
        return 0.0

    @property
    def _feature_shape_object_normalized_moment_x_y(self):
        return 0.0

    @property
    def _feature_shape_object_orientation(self):
        return 0.0

    @property
    def _feature_shape_object_perimeter(self):
        return 0.0

    @property
    def _feature_shape_object_solidity(self):
        return 0.0

    @property
    def _feature_shape_object_spatial_moment_0_0_0(self):
        return self.spatial_moments[0, 0, 0]

    @property
    def _feature_shape_object_spatial_moment_0_0_1(self):
        return self.spatial_moments[0, 0, 1]

    @property
    def _feature_shape_object_spatial_moment_0_0_2(self):
        return self.spatial_moments[0, 0, 2]

    @property
    def _feature_shape_object_spatial_moment_0_0_3(self):
        return self.spatial_moments[0, 0, 3]

    @property
    def _feature_shape_object_spatial_moment_0_1_0(self):
        return self.spatial_moments[0, 1, 0]

    @property
    def _feature_shape_object_spatial_moment_0_1_1(self):
        return self.spatial_moments[0, 1, 1]

    @property
    def _feature_shape_object_spatial_moment_0_1_2(self):
        return self.spatial_moments[0, 1, 2]

    @property
    def _feature_shape_object_spatial_moment_0_1_3(self):
        return self.spatial_moments[0, 1, 3]

    @property
    def _feature_shape_object_spatial_moment_0_2_0(self):
        return self.spatial_moments[0, 2, 0]

    @property
    def _feature_shape_object_spatial_moment_0_2_1(self):
        return self.spatial_moments[0, 2, 1]

    @property
    def _feature_shape_object_spatial_moment_0_2_2(self):
        return self.spatial_moments[0, 2, 2]

    @property
    def _feature_shape_object_spatial_moment_0_2_3(self):
        return self.spatial_moments[0, 2, 3]

    @property
    def _feature_shape_object_spatial_moment_0_3_0(self):
        return self.spatial_moments[0, 3, 0]

    @property
    def _feature_shape_object_spatial_moment_0_3_1(self):
        return self.spatial_moments[0, 3, 1]

    @property
    def _feature_shape_object_spatial_moment_0_3_2(self):
        return self.spatial_moments[0, 3, 2]

    @property
    def _feature_shape_object_spatial_moment_0_3_3(self):
        return self.spatial_moments[0, 3, 3]

    @property
    def _feature_shape_object_spatial_moment_1_0_0(self):
        return self.spatial_moments[1, 0, 0]

    @property
    def _feature_shape_object_spatial_moment_1_0_1(self):
        return self.spatial_moments[1, 0, 1]

    @property
    def _feature_shape_object_spatial_moment_1_0_2(self):
        return self.spatial_moments[1, 0, 2]

    @property
    def _feature_shape_object_spatial_moment_1_0_3(self):
        return self.spatial_moments[1, 0, 3]

    @property
    def _feature_shape_object_spatial_moment_1_1_0(self):
        return self.spatial_moments[1, 1, 0]

    @property
    def _feature_shape_object_spatial_moment_1_1_1(self):
        return self.spatial_moments[1, 1, 1]

    @property
    def _feature_shape_object_spatial_moment_1_1_2(self):
        return self.spatial_moments[1, 1, 2]

    @property
    def _feature_shape_object_spatial_moment_1_1_3(self):
        return self.spatial_moments[1, 1, 3]

    @property
    def _feature_shape_object_spatial_moment_1_2_0(self):
        return self.spatial_moments[1, 2, 0]

    @property
    def _feature_shape_object_spatial_moment_1_2_1(self):
        return self.spatial_moments[1, 2, 1]

    @property
    def _feature_shape_object_spatial_moment_1_2_2(self):
        return self.spatial_moments[1, 2, 2]

    @property
    def _feature_shape_object_spatial_moment_1_2_3(self):
        return self.spatial_moments[1, 2, 3]

    @property
    def _feature_shape_object_spatial_moment_1_3_0(self):
        return self.spatial_moments[1, 3, 0]

    @property
    def _feature_shape_object_spatial_moment_1_3_1(self):
        return self.spatial_moments[1, 3, 1]

    @property
    def _feature_shape_object_spatial_moment_1_3_2(self):
        return self.spatial_moments[1, 3, 2]

    @property
    def _feature_shape_object_spatial_moment_1_3_3(self):
        return self.spatial_moments[1, 3, 3]

    @property
    def _feature_shape_object_spatial_moment_2_0_0(self):
        return self.spatial_moments[2, 0, 0]

    @property
    def _feature_shape_object_spatial_moment_2_0_1(self):
        return self.spatial_moments[2, 0, 1]

    @property
    def _feature_shape_object_spatial_moment_2_0_2(self):
        return self.spatial_moments[2, 0, 2]

    @property
    def _feature_shape_object_spatial_moment_2_0_3(self):
        return self.spatial_moments[2, 0, 3]

    @property
    def _feature_shape_object_spatial_moment_2_1_0(self):
        return self.spatial_moments[2, 1, 0]

    @property
    def _feature_shape_object_spatial_moment_2_1_1(self):
        return self.spatial_moments[2, 1, 1]

    @property
    def _feature_shape_object_spatial_moment_2_1_2(self):
        return self.spatial_moments[2, 1, 2]

    @property
    def _feature_shape_object_spatial_moment_2_1_3(self):
        return self.spatial_moments[2, 1, 3]

    @property
    def _feature_shape_object_spatial_moment_2_2_0(self):
        return self.spatial_moments[2, 2, 0]

    @property
    def _feature_shape_object_spatial_moment_2_2_1(self):
        return self.spatial_moments[2, 2, 1]

    @property
    def _feature_shape_object_spatial_moment_2_2_2(self):
        return self.spatial_moments[2, 2, 2]

    @property
    def _feature_shape_object_spatial_moment_2_2_3(self):
        return self.spatial_moments[2, 2, 3]

    @property
    def _feature_shape_object_spatial_moment_2_3_0(self):
        return self.spatial_moments[2, 3, 0]

    @property
    def _feature_shape_object_spatial_moment_2_3_1(self):
        return self.spatial_moments[2, 3, 1]

    @property
    def _feature_shape_object_spatial_moment_2_3_2(self):
        return self.spatial_moments[2, 3, 2]

    @property
    def _feature_shape_object_spatial_moment_2_3_3(self):
        return self.spatial_moments[2, 3, 3]

    @property
    def _feature_shape_object_spatial_moment_3_0_0(self):
        return self.spatial_moments[3, 0, 0]

    @property
    def _feature_shape_object_spatial_moment_3_0_1(self):
        return self.spatial_moments[3, 0, 1]

    @property
    def _feature_shape_object_spatial_moment_3_0_2(self):
        return self.spatial_moments[3, 0, 2]

    @property
    def _feature_shape_object_spatial_moment_3_0_3(self):
        return self.spatial_moments[3, 0, 3]

    @property
    def _feature_shape_object_spatial_moment_3_1_0(self):
        return self.spatial_moments[3, 1, 0]

    @property
    def _feature_shape_object_spatial_moment_3_1_1(self):
        return self.spatial_moments[3, 1, 1]

    @property
    def _feature_shape_object_spatial_moment_3_1_2(self):
        return self.spatial_moments[3, 1, 2]

    @property
    def _feature_shape_object_spatial_moment_3_1_3(self):
        return self.spatial_moments[3, 1, 3]

    @property
    def _feature_shape_object_spatial_moment_3_2_0(self):
        return self.spatial_moments[3, 2, 0]

    @property
    def _feature_shape_object_spatial_moment_3_2_1(self):
        return self.spatial_moments[3, 2, 1]

    @property
    def _feature_shape_object_spatial_moment_3_2_2(self):
        return self.spatial_moments[3, 2, 2]

    @property
    def _feature_shape_object_spatial_moment_3_2_3(self):
        return self.spatial_moments[3, 2, 3]

    @property
    def _feature_shape_object_spatial_moment_3_3_0(self):
        return self.spatial_moments[3, 3, 0]

    @property
    def _feature_shape_object_spatial_moment_3_3_1(self):
        return self.spatial_moments[3, 3, 1]

    @property
    def _feature_shape_object_spatial_moment_3_3_2(self):
        return self.spatial_moments[3, 3, 2]

    @property
    def _feature_shape_object_spatial_moment_3_3_3(self):
        return self.spatial_moments[3, 3, 3]

    @property
    def _feature_shape_object_surface_area(self):
        return 0.0

    @property
    def _feature_shape_object_volume(self):
        return 0.0

    # Shape: Object skeleton

    @property
    def _feature_shape_object_skeleton_endpoints(self):
        return 0.0

    @property
    def _feature_shape_object_skeleton_branches(self):
        return 0.0

    @property
    def _feature_shape_object_skeleton_length(self):
        return 0.0

    @property
    def _feature_shape_object_skeleton_trunks(self):
        return 0.0

    # Texture

    # Texture: Object

    @property
    def _feature_texture_object_haralick_angular_second_moment(self):
        return 0.0

    @property
    def _feature_texture_object_haralick_contrast(self):
        return 0.0

    @property
    def _feature_texture_object_haralick_coorelation(self):
        return 0.0

    @property
    def _feature_texture_object_haralick_sum_of_squares_variance(self):
        return 0.0

    @property
    def _feature_texture_object_haralick_inverse_difference_moment(self):
        return 0.0

    @property
    def _feature_texture_object_haralick_sum_average(self):
        return 0.0

    @property
    def _feature_texture_object_haralick_sum_variance(self):
        return 0.0

    @property
    def _feature_texture_object_haralick_sum_entropy(self):
        return 0.0

    @property
    def _feature_texture_object_haralick_entropy(self):
        return 0.0

    @property
    def _feature_texture_object_haralick_difference_variance(self):
        return 0.0

    @property
    def _feature_texture_object_haralick_measure_of_correlation_0(self):
        return 0.0

    @property
    def _feature_texture_object_haralick_measure_of_correlation_1(self):
        return 0.0

    @property
    def _feature_texture_object_haralick_maximum_correlation_coefficient(self):
        return 0.0

    @property
    def _members(self):
        members = inspect.getmembers(self.__class__, lambda member: isinstance(member, property))

        return sorted([k for k, _ in members if k.startswith("_feature_")])
