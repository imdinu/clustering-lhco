import numpy as np
from pyjet import cluster, DTYPE_PTEPM

(pT_i, rap_i, phi_i) = (0, 1, 2)
"""tuple: interpretation of the input array coulmn numbers

The columns represented are:
 * ``pT_i``: transverse momentum
 * ``rap_i``: (pseudo)rapidity
 * ``phi_i``: azimuthal angle
"""

default_options = {

        'fcut': 0.05,   
        'R1': 1.0,      
        'R2': 0.2,    
        'offset': 0.5,  
}
"""dict: default image generation options

The keys represent:
 * ``fcut``: fraction of main cluster pT required for subjet to pass trimming
 * ``R1``: radius of the main jet cluster
 * ``R2``: radius of the secondary clusters
 * ``offset``: pivot offset from bottom axis, relative to the image width
"""

def average_centroid(jet, npix, pix_width):
    """Jet image indexes whitc cenetering on the average centroid

    Args:
        jet (np.array): An array of particles where each particle is of the 
        form `[pt,y,phi]` 
    npix (int): the number of pixels on one edge of the jet image, which 
        is presumed to be a square.
    pix_width (float): the size of one pixel of the jet image in the 
        rapidity-azimuth plane.
    Returns:
        rap_indices, phi_indices: indices used for pixelation
    """
    rap_avg = np.average(jet[:,rap_i], weights=jet[:,pT_i])
    phi_avg = np.average(jet[:,phi_i], weights=jet[:,pT_i])
    rap_pt_cent_index = np.ceil(rap_avg/pix_width - 0.5) - np.floor(npix / 2)
    phi_pt_cent_index = np.ceil(phi_avg/pix_width - 0.5) - np.floor(npix / 2)
    rap_indices = np.ceil(jet[:,rap_i]/pix_width - 0.5) - rap_pt_cent_index
    phi_indices = np.ceil(jet[:,phi_i]/pix_width - 0.5) - phi_pt_cent_index

    return rap_indices, phi_indices

def trim_jet(pseudojets_input, subjet_array, R, fcut):
    """Applies jet trimming based on arguments.

    Args:
        pseudojets_input (np.ndarray): constituents array compatible with 
            ``pyjet`` clustering
        subjet_array (list): collection of ``pyjet.PseudoJet`` objects 
            obtained from secondary clustering
        R (float): radius of the main jet cluster
        fcut (float): fraction of main cluster pT required for subjet to 
            pass trimming

    Returns:
        constituents array of the jet, after trimming
    """
    trimmed_jet = []
    for subjet in subjet_array:
        # get main cluster pt
        main_cluster = cluster(pseudojets_input, R=R, p=-1)
        parent_pt = main_cluster.inclusive_jets()[0].pt

        if subjet.pt > parent_pt * fcut:
            # Get the subjets pt, eta, phi constituents
            subjet_data = subjet.constituents_array()
            subjet_data = subjet_data.view((float, 
                            len(subjet_data.dtype.names))
                        )
            trimmed_jet.append(subjet_data)
    return np.concatenate(trimmed_jet)[:,:3]

def make_image(jet, rap_indices, phi_indices, npix):
    """Creates a jet image using indices in ``y`` and ``phi``.

    Args:
        jet (np.ndarray): constituents array of the jet
        rap_indices (np.ndarray): rapidiy indices of the image
        phi_indices (np.ndarray): phy indices of the image
        npix (int): image width or height in pixels

    Return:
        2D ``np.ndarray`` jet image 
    """

    # delete elements outside of range
    mask = np.ones(jet[:,rap_i].shape).astype(bool)
    mask[rap_indices < 0] = False
    mask[phi_indices < 0] = False
    mask[rap_indices >= npix] = False
    mask[phi_indices >= npix] = False
    rap_indices = rap_indices[mask].astype(int)
    phi_indices = phi_indices[mask].astype(int)
    
    jet_image = np.zeros((npix, npix, 1))

    # construct grayscale image
    for pt,y,phi in zip(jet[:,pT_i][mask], rap_indices, phi_indices): 
        jet_image[phi, y, 0] += pt
    
    return jet_image

def pseudojet(jet):
    """Returns a numpy array of dtype ``DTYPE_PTEPM``

    Args:
        jet: array of particles where each particle is of the form 
            ``[pt,y,phi]``

    Returns:
        np.ndarray compatible with ``pyjet`` clustering
    """
    pseudojets_input = np.zeros(jet.shape[0], dtype=DTYPE_PTEPM)
    pseudojets_input['pT'] = jet[:,pT_i]
    pseudojets_input['eta'] = jet[:,rap_i]
    pseudojets_input['phi'] = jet[:,phi_i]

    return pseudojets_input

def transform(jet, subjet_array, img_width, pix_width, rotate, offset):
    """Returns the y and phy indices of the image after rotation and offsets.

    Args:
        jet (np.ndarray): constituents array of the jet
        subjet_array (list): collection of ``pyjet.PseudoJet`` objects 
            obtained from secondary clustering
        img_width (float): the size of one edge of the jet image in the 
            rapidity-azimuth plane
        pix_width (float): the size of one pixel of the jet image in the 
            rapidity-azimuth plane
        rotate (bool): perform rotation, alligning the top 2 leading-pT
            secondary clusters on the vertival axis
        offset (float): relative position of the most energetic cluster
            with respect to the bottom edge of the image; a vlaue of 0.5
            will result in this cluster being perfectly cenetered 
    Returns:
        rap_indices, phi_indices: indices used for pixelation
    """
    # define pivot and edge coordinates
    rap_p = subjet_array[0].eta
    phi_p = subjet_array[0].phi
    if len(subjet_array) < 2:
        rotate = False
    else:
        rap_e = subjet_array[1].eta
        phi_e = subjet_array[1].phi
    new_origin = np.array([0, rap_p, phi_p])
    
    # translate jet to put pivot in origin (0, 0)
    jet = jet-new_origin


    if rotate:
        # compute the unit vector of the edge
        r = np.array([rap_p-rap_e, phi_p-phi_e])
        ur = r/np.linalg.norm(r)

        # define vertical axis unit vector 
        uy = np.array([0, 1])

        # rotation angle for bringing edge on the certical axis
        theta = np.arccos(np.dot(uy, ur))*(np.sign(ur[0]))
        
        # anticlockwise rotation matrix
        rotate2d = np.array([[np.cos(theta), np.sin(theta)],
                            [-np.sin(theta), np.cos(theta)]])

        # apply rotation to all jet constituents' coordinates
        jet[:,1:] = np.dot(jet[:,1:],rotate2d)

    # translate to place pivot according to offset
    jet =  jet+np.array([0, img_width/2, img_width*offset])

    # transistion to indices 
    rap_indices = np.ceil(jet[:,rap_i]/pix_width - 0.5) 
    phi_indices = np.ceil(jet[:,phi_i]/pix_width - 0.5)

    return rap_indices, phi_indices


def pixelate(jet, 
             npix=32, 
             img_width=0.8, 
             trim=False,
             norm=False, 
             avg_centroid=False,
             rotate=True,
             **kwargs):
    """A function for creating a jet image from an array of particles.
    
    Args:
        jet (np.array): An array of particles where each particle is of the 
            form `[pt,y,phi]` 
        npix (int): the number of pixels on one edge of the jet image, which 
            is presumed to be a square.
        img_width (float): the size of one edge of the jet image in the 
            rapidity-azimuth plane.
        trim (bool): wheter or not to apply jet trimming based on options
        avg_centroid (bool): center the image based on the average pT centroid
        rotate (bool) :rotate image to align leading secondary clusters on the 
            vertical
        norm (bool) whether or not to normalize the $p_T$ pixels to sum to `1`
    
    Return:
        `np.ndarray` jet image of shape `(npix, npix, 1)`
    """

    # read **kwargs and overwrite any default option values
    options = default_options.copy()
    options.update(kwargs)

    # the image is (img_width x img_width) in size
    pix_width = img_width / npix

    # pseudojet inputs necessary for `pyjet` clustering
    pseudojets_input = pseudojet(jet)

    # remove particles with zero pt
    jet = jet[jet[:,pT_i] > 0]

    if avg_centroid:
        if rotate:
            raise NotImplementedError("Rotation only available when "
                                      "avg_centroid=False")
        if trim:
            sequence = cluster(pseudojets_input, R=options["R1"], p=1)
            subjet_array = sequence.inclusive_jets()
            jet = trim_jet(pseudojets_input, subjet_array, 
                        options["R1"], options["fcut"])
        rap_indices, phi_indices = average_centroid(jet, npix, pix_width)

    else:
        sequence = cluster(pseudojets_input, R=options["R1"], p=1)
        subjet_array = sequence.inclusive_jets()
        if trim:
            jet = trim_jet(pseudojets_input, subjet_array, 
                        options["R1"], options["fcut"])
        rap_indices, phi_indices = transform(jet, subjet_array, 
                                             img_width, pix_width,
                                             rotate, options["offset"])


    jet_image = make_image(jet, rap_indices, phi_indices, npix)

    # L1-normalize the pt channels of the jet image
    if norm:
        normfactor = np.sum(jet_image[...,pT_i])
        if normfactor == 0:
            raise FloatingPointError('Image had no particles!')
        else: 
            jet_image[...,0] /= normfactor

    return jet_image 

def image_from_jets(jets, stitch_jets=False, **kwargs):
    """Given an array of clustered jets, creates a jet image.

    Args:
        jets (list): collection of jets to be pixelated
        stitch_jets (bool): represents all jets in the same image; when 
            ``False`` every jet will be represented as a different channel
        **kwargs: parameters for jet image generation

    Return:
        np.ndarray of jet image. 2-D if ``stitch_jets`` is ``True``, otherwise
        3-D array
    """
    if stitch_jets:
        arr = np.concatenate([_jet_to_array(x) for x in jets if x is not None])
        img = np.asarray(pixelate(arr, **kwargs))
    else:
        arr = [pixelate(_jet_to_array(x), **kwargs) 
                        for x in jets 
                        if x is not None]
        arr = np.squeeze(np.asarray(arr),-1)
        img = np.moveaxis(arr, 0, -1)
        njets = len(jets)
        missing_jets = njets - img.shape[2]
        npix = img.shape[0]
        if missing_jets>0:
            padding = np.zeros(shape=(npix,npix,missing_jets))
            img = np.concatenate([img, padding], axis=2)
    return img

def _jet_to_array(jet):
    constit = jet.constituents_array()
    return constit.view((float, len(constit.dtype.names)))[:,:3]