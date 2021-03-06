import os
from functools import wraps
from typing import List

import cv2
import numpy as np
import pytest

from lr_face.data import (FaceImage,
                          FacePair,
                          FaceTriplet,
                          DummyFaceImage,
                          EnfsiDataset,
                          ForenFaceDataset,
                          LfwDataset,
                          make_pairs,
                          make_triplets,
                          to_array,
                          split_by_identity)
from tests.conftest import skip_on_github
from tests.src.util import get_project_path, scratch_dir


def dataset_testable(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        dataset = func(*args, **kwargs)
        if hasattr(dataset, 'RESOURCE_FOLDER'):
            dataset.RESOURCE_FOLDER = get_project_path(dataset.RESOURCE_FOLDER)
        return dataset

    return wrapper


def augmenter(image: np.ndarray) -> np.ndarray:
    """
    Dummy augmenter that makes each image completely black
    """
    return np.zeros(image.shape)


@pytest.fixture
def dummy_images() -> List[FaceImage]:
    ids = [1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5]
    return [DummyFaceImage(path='', identity=f'TEST-{idx}') for idx in ids]


@pytest.fixture
def dummy_pairs() -> List[FacePair]:
    ids = [1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5]
    images = [DummyFaceImage(path='', identity=f'TEST-{idx}') for idx in ids]
    return make_pairs(images)


@pytest.fixture
def dummy_triplets() -> List[FaceTriplet]:
    ids = [1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5]
    images = [DummyFaceImage(path='', identity=f'TEST-{idx}') for idx in ids]
    return make_triplets(images)


@pytest.fixture
@dataset_testable
def enfsi_2011():
    return EnfsiDataset(years=[2011])


@pytest.fixture
@dataset_testable
def enfsi_all():
    return EnfsiDataset(years=[2011, 2012, 2013, 2017])


@pytest.fixture
@dataset_testable
def forenface():
    return ForenFaceDataset()


@pytest.fixture
@dataset_testable
def lfw():
    return LfwDataset()


@pytest.fixture()
def scratch():
    yield from scratch_dir('scratch/test_data')


###############
# `FaceImage` #
###############

def test_get_image(dummy_images, scratch):
    width = 100
    height = 50
    resolution = (height, width)
    image = dummy_images[0].get_image(resolution, normalize=False)
    image_path = os.path.join(scratch, 'tmp.jpg')
    cv2.imwrite(image_path, image)
    face_image = FaceImage(image_path, dummy_images[0].identity)
    reloaded_image = face_image.get_image(resolution)
    assert reloaded_image.shape == (*resolution, 3)


#################
# `FaceTriplet` #
#################

def test_face_triplet_raises_exception_on_wrong_identities():
    anchor = FaceImage('', identity='A')
    false_positive = FaceImage('', identity='B')
    true_positive = FaceImage('', identity='A')
    false_negative = FaceImage('', identity='A')
    true_negative = FaceImage('', identity='B')
    with pytest.raises(ValueError):
        FaceTriplet(anchor, false_positive, true_negative)
    with pytest.raises(ValueError):
        FaceTriplet(anchor, true_positive, false_negative)
    with pytest.raises(ValueError):
        FaceTriplet(anchor, false_positive, false_negative)


################
# `LfwDataset` #
################

@skip_on_github
def test_lfw_dataset_has_correct_num_images(lfw):
    assert len(lfw.images) == 13233


@skip_on_github
def test_lfw_dataset_has_correct_num_pairs(lfw):
    assert len(lfw.pairs) == 6000


##################
# `EnfsiDataset` #
##################

@skip_on_github
def test_enfsi_dataset_has_correct_num_images(enfsi_all):
    assert len(enfsi_all.images) == 270


@skip_on_github
def test_enfsi_dataset_has_correct_num_pairs(enfsi_all):
    assert len(enfsi_all.pairs) == 135
    assert all([a.meta['idx'] == b.meta['idx'] for a, b in enfsi_all.pairs])


###############
# `ForenFace` #
###############

@skip_on_github
def test_forenface_dataset_has_correct_num_images(forenface):
    assert len(forenface.images) == 2476


##################
# `make_pairs()` #
##################

def test_make_pairs_positive_and_negative_no_n(dummy_images):
    pairs = make_pairs(dummy_images, same=None, n=None)
    positive_pairs = [p for p in pairs if p.same_identity]
    negative_pairs = [p for p in pairs if not p.same_identity]
    assert len(positive_pairs) == len(negative_pairs) == 8
    assert positive_pairs[0].first.identity == 'TEST-1'
    assert positive_pairs[1].first.identity == 'TEST-1'
    assert positive_pairs[2].first.identity == 'TEST-1'
    assert positive_pairs[3].first.identity == 'TEST-2'
    assert positive_pairs[4].first.identity == 'TEST-2'
    assert positive_pairs[5].first.identity == 'TEST-2'
    assert positive_pairs[6].first.identity == 'TEST-3'
    assert positive_pairs[7].first.identity == 'TEST-4'


def test_make_pairs_positive_and_negative_fixed_n(dummy_images):
    n = 8
    pairs = make_pairs(dummy_images, same=None, n=n)
    assert len(pairs) == n


def test_make_pairs_positive_and_negative_fixed_n_odd(dummy_images):
    n = 7
    pairs = make_pairs(dummy_images, same=None, n=n)
    assert len(pairs) == n


def test_make_pairs_positive_and_negative_large_n(dummy_images):
    n = 10000
    pairs = make_pairs(dummy_images, same=None, n=n)
    assert len(pairs) == 16


def test_make_pairs_positive_only_no_n(dummy_images):
    pairs = make_pairs(dummy_images, same=True, n=None)
    positive_pairs = [p for p in pairs if p.same_identity]
    assert len(positive_pairs) == len(pairs) == 8
    assert positive_pairs[0].first.identity == 'TEST-1'
    assert positive_pairs[1].first.identity == 'TEST-1'
    assert positive_pairs[2].first.identity == 'TEST-1'
    assert positive_pairs[3].first.identity == 'TEST-2'
    assert positive_pairs[4].first.identity == 'TEST-2'
    assert positive_pairs[5].first.identity == 'TEST-2'
    assert positive_pairs[6].first.identity == 'TEST-3'
    assert positive_pairs[7].first.identity == 'TEST-4'


def test_make_pairs_positive_only_fixed_n(dummy_images):
    n = 8
    pairs = make_pairs(dummy_images, same=True, n=n)
    positive_pairs = [p for p in pairs if p.same_identity]
    assert len(positive_pairs) == len(pairs) == 8


def test_make_pairs_positive_only_fixed_n_odd(dummy_images):
    n = 7
    pairs = make_pairs(dummy_images, same=True, n=n)
    positive_pairs = [p for p in pairs if p.same_identity]
    assert len(positive_pairs) == len(pairs) == 7


def test_make_pairs_positive_only_large_n(dummy_images):
    n = 10000
    pairs = make_pairs(dummy_images, same=True, n=n)
    positive_pairs = [p for p in pairs if p.same_identity]
    assert len(positive_pairs) == len(pairs) == 8


def test_make_pairs_negative_only_no_n(dummy_images):
    pairs = make_pairs(dummy_images, same=False, n=None)
    negative_pairs = [p for p in pairs if not p.same_identity]
    assert len(negative_pairs) == len(pairs) == 94
    assert negative_pairs[0].first.identity == 'TEST-1'
    assert negative_pairs[24].first.identity == 'TEST-2'
    assert negative_pairs[48].first.identity == 'TEST-3'
    assert negative_pairs[66].first.identity == 'TEST-4'
    assert negative_pairs[84].first.identity == 'TEST-5'


def test_make_pairs_negative_only_fixed_n(dummy_images):
    n = 48
    pairs = make_pairs(dummy_images, same=False, n=n)
    negative_pairs = [p for p in pairs if not p.same_identity]
    assert len(negative_pairs) == len(pairs) == n


def test_make_pairs_negative_only_fixed_n_odd(dummy_images):
    n = 47
    pairs = make_pairs(dummy_images, same=False, n=n)
    negative_pairs = [p for p in pairs if not p.same_identity]
    assert len(negative_pairs) == len(pairs) == n


def test_make_pairs_negative_only_large_n(dummy_images):
    n = 10000
    pairs = make_pairs(dummy_images, same=False, n=n)
    negative_pairs = [p for p in pairs if not p.same_identity]
    assert len(negative_pairs) == len(pairs) == n


##################
# `EnfsiDataset` #
##################

@skip_on_github
def test_enfsi_dataset_has_correct_num_images(enfsi_all):
    assert len(enfsi_all.images) == 270


@skip_on_github
def test_enfsi_dataset_has_correct_num_pairs(enfsi_all):
    assert len(enfsi_all.pairs) == 135
    assert all([a.meta['idx'] == b.meta['idx'] for a, b in enfsi_all.pairs])


###############
# `ForenFace` #
###############

@skip_on_github
def test_forenface_dataset_has_correct_num_images(forenface):
    assert len(forenface.images) == 2476


#####################
# `make_triplets()` #
#####################

def test_make_triplets_one_pair_per_identity():
    n = 10
    data = [DummyFaceImage('', str(i // 2)) for i in range(n)]
    triplets = make_triplets(data)
    assert len(triplets) == 5
    for i, (anchor, positive, negative) in enumerate(triplets):
        assert anchor is data[2 * i]
        assert positive is data[2 * i + 1]


def test_make_triplets_six_pairs_per_identity():
    n = 40
    data = [DummyFaceImage('', str(i // 4)) for i in range(n)]
    triplets = make_triplets(data)
    assert len(triplets) == 60


################
# `to_array()` #
################

def test_face_images_to_array(dummy_images):
    resolution = (50, 100)
    array = to_array(dummy_images, resolution=resolution)
    assert array.shape == (len(dummy_images), *resolution, 3)


def test_face_images_to_array_with_various_resolutions(dummy_images, scratch):
    face_images = []
    for i, dummy_image in enumerate(dummy_images):
        image = dummy_image.get_image(normalize=False)
        dimensions = (50 + i, 100)
        image = cv2.resize(image, dimensions)
        image_path = os.path.join(scratch, f'tmp_{i}.jpg')
        cv2.imwrite(image_path, image)
        face_images.append(FaceImage(image_path, dummy_images[0].identity))

    # Should raise an exception, because we do not allow `to_array` to accept
    # images of various shapes.
    with pytest.raises(ValueError):
        to_array(face_images)


def test_zero_face_images_to_array():
    with pytest.raises(ValueError):
        to_array([])


def test_face_pairs_to_array(dummy_pairs):
    resolution = (50, 100)
    left, right = to_array(dummy_pairs, resolution=resolution)
    expected_shape = (len(dummy_pairs), *resolution, 3)
    assert left.shape == expected_shape
    assert right.shape == expected_shape


def test_face_triplets_to_array(dummy_triplets):
    resolution = (50, 100)
    anchors, positives, negatives = to_array(
        dummy_triplets,
        resolution=resolution
    )
    expected_shape = (len(dummy_triplets), *resolution, 3)
    assert anchors.shape == expected_shape
    assert positives.shape == expected_shape
    assert negatives.shape == expected_shape


def test_face_images_to_array_with_augmenter(dummy_images):
    resolution = (50, 50)
    expected_shape = (len(dummy_images), *reversed(resolution), 3)
    array = to_array(dummy_images, resolution, augmenter=None)
    assert array.shape == expected_shape
    assert not np.all(array == 0)
    augmented = to_array(dummy_images, resolution, augmenter=augmenter)
    assert augmented.shape == expected_shape
    assert np.all(augmented == 0)


def test_face_pairs_to_array_with_augmenters(dummy_pairs):
    resolution = (50, 50)
    expected_shape = (len(dummy_pairs), *reversed(resolution), 3)
    a, b = to_array(dummy_pairs, resolution, augmenter=None)
    assert a.shape == expected_shape
    assert b.shape == expected_shape
    assert not np.all(a == 0)
    assert not np.all(b == 0)
    a_augmented, b_augmented = \
        to_array(dummy_pairs, resolution, augmenter=(augmenter, augmenter))
    assert a_augmented.shape == expected_shape
    assert b_augmented.shape == expected_shape
    assert np.all(a_augmented == 0)
    assert np.all(b_augmented == 0)


def test_face_pairs_to_array_with_single_augmenter(dummy_pairs):
    resolution = (50, 50)
    a, b = to_array(dummy_pairs, resolution, augmenter=None)
    assert not np.all(a == 0)
    assert not np.all(b == 0)
    a_augmented, b_augmented = \
        to_array(dummy_pairs, resolution, augmenter=augmenter)
    assert np.all(a_augmented == 0)
    assert np.all(b_augmented == 0)


def test_face_pairs_to_array_with_augmenter_only_first(dummy_pairs):
    resolution = (50, 50)
    a, b = to_array(dummy_pairs, resolution, augmenter=None)
    assert not np.all(a == 0)
    assert not np.all(b == 0)
    a_augmented, b_augmented = \
        to_array(dummy_pairs, resolution, augmenter=(augmenter, None))
    assert np.all(a_augmented == 0)
    assert np.all(b == b_augmented)


def test_face_triplets_to_array_with_augmenters(dummy_triplets):
    resolution = (50, 50)
    expected_shape = (len(dummy_triplets), *reversed(resolution), 3)
    anchors, positives, negatives = to_array(
        dummy_triplets,
        resolution,
        augmenter=None
    )
    assert anchors.shape == expected_shape
    assert positives.shape == expected_shape
    assert negatives.shape == expected_shape
    assert not np.all(anchors == 0)
    assert not np.all(positives == 0)
    assert not np.all(negatives == 0)
    anchors_augmented, positives_augmented, negatives_augmented = to_array(
        dummy_triplets,
        resolution,
        augmenter=(augmenter, augmenter, augmenter)
    )
    assert anchors_augmented.shape == expected_shape
    assert positives_augmented.shape == expected_shape
    assert negatives_augmented.shape == expected_shape
    assert np.all(anchors_augmented == 0)
    assert np.all(positives_augmented == 0)
    assert np.all(negatives_augmented == 0)


def test_face_triplets_to_array_with_single_augmenter(dummy_triplets):
    resolution = (50, 50)
    anchors, positives, negatives = to_array(
        dummy_triplets,
        resolution,
        augmenter=None
    )
    assert not np.all(anchors == 0)
    assert not np.all(positives == 0)
    assert not np.all(negatives == 0)
    anchors_augmented, positives_augmented, negatives_augmented = to_array(
        dummy_triplets,
        resolution,
        augmenter=augmenter
    )
    assert np.all(anchors_augmented == 0)
    assert np.all(positives_augmented == 0)
    assert np.all(negatives_augmented == 0)


def test_face_triplets_to_array_with_augmenter_only_anchor(dummy_triplets):
    resolution = (50, 50)
    anchors, positives, negatives = to_array(
        dummy_triplets,
        resolution,
        augmenter=None
    )
    assert not np.all(anchors == 0)
    assert not np.all(positives == 0)
    assert not np.all(negatives == 0)
    anchors_augmented, positives_augmented, negatives_augmented = to_array(
        dummy_triplets,
        resolution,
        augmenter=(augmenter, None, None)
    )
    assert np.all(anchors_augmented == 0)
    assert np.all(positives == positives_augmented)
    assert np.all(negatives == negatives_augmented)


#########################
# `split_by_identity()` #
#########################

def test_split_by_identity(dummy_images):
    """
    Tests that `split_by_identity` results in two disjoint sets of images in
    terms of their identity.
    """

    # Since the results are random we run the test 10 times.
    for _ in range(10):
        train, test = split_by_identity(
            dummy_images,
            test_size=0.2
        )

        unique_train_identities = set(x.identity for x in train)
        unique_test_identities = set(x.identity for x in test)
        assert not unique_train_identities.intersection(unique_test_identities)
