

import errno
import os
import shutil  ## needed for removing directory tree
from builtins import range

# Globals
POSTERIORS = ['WM', 'SURFGM', 'BASAL', 'GLOBUS', 'THALAMUS',
              'HIPPOCAMPUS', 'CRBLGM', 'CRBLWM', 'CSF', 'VB', 'NOTCSF', 'NOTGM', 'NOTWM',
              'NOTVB', 'AIR']


def convertToList(element):
    if element is None:
        return ''
    return [element]


def MakeInclusionMaskForGMStructures(posteriorDictionary, candidateRegionFileName):
    import SimpleITK as sitk

    AIR_FN = posteriorDictionary['AIR']
    CSF_FN = posteriorDictionary['CSF']
    VB_FN = posteriorDictionary['VB']
    WM_FN = posteriorDictionary['WM']

    AIR_PROB = sitk.ReadImage(AIR_FN)
    CSF_PROB = sitk.ReadImage(CSF_FN)
    VB_PROB = sitk.ReadImage(VB_FN)
    WM_PROB = sitk.ReadImage(WM_FN)

    AIR_Region = sitk.BinaryThreshold(AIR_PROB, 0.51, 1.01, 1, 0)
    CSF_Region = sitk.BinaryThreshold(CSF_PROB, 0.51, 1.01, 1, 0)
    VB_Region = sitk.BinaryThreshold(VB_PROB, 0.51, 1.01, 1, 0)
    WM_Region = sitk.BinaryThreshold(WM_PROB, 0.99, 1.01, 1, 0)  # NOTE: Higher tolerance for WM regions!

    outputCandidateRegion = sitk.BinaryThreshold(AIR_Region + CSF_Region + VB_Region + WM_Region, 1, 100, 0,
                                                 1)  # NOTE: Inversion of input/output definitions
    ##  Now write out the candidate region name.
    import os
    outputCandidateRegionFileName = os.path.realpath(candidateRegionFileName)
    sitk.WriteImage(outputCandidateRegion, outputCandidateRegionFileName)

    return outputCandidateRegionFileName


def makeListOfValidImages(imageFile):
    if imageFile is None:
        return []  # an empty iterable is a valid input to a data string
    else:
        return imageFile


# def makeStringForMissingImages(imageFile):
#     if imageFile is None:
#         return ''  # DataSinks fail for empty lists
#     else:
#         return imageFile

def getListIndex(imageList, index):
    return imageList[index]


def ClipT1ImageWithBrainMask(t1_image, brain_labels, clipped_file_name):
    import os
    import sys
    import SimpleITK as sitk
    ## Now clean up the posteriors based on anatomical knowlege.
    ## sometimes the posteriors are not relevant for priors
    ## due to anomolies around the edges.
    t1 = sitk.Cast(sitk.ReadImage(t1_image), sitk.sitkFloat32)
    bl = sitk.Cast(sitk.ReadImage(brain_labels), sitk.sitkFloat32)
    bl_binary = sitk.Cast(sitk.BinaryThreshold(bl, 1, 1000000), sitk.sitkFloat32)
    clipped = t1 * bl_binary
    sitk.WriteImage(clipped, clipped_file_name)
    clipped_file = os.path.realpath(clipped_file_name)
    return clipped_file


def UnwrapPosteriorImagesFromDictionaryFunction(postDict):
    ## Dictionary values are now being returned as unicode characters
    ## so convert back to ascii
    return [x for x in list(postDict.values())]


def ConvertSessionsListOfPosteriorListToDictionaryOfSessionLists(dg_list_list):
    """ The input is a list of sessions with a list of posteriors per session.
        The output is a dicitionary of posterior types, with a list of that
        posterior type for each session.

        dg_list_list=[['Y1/POSTERIOR_AIR.nii.gz','Y1/POSTERIOR_CAUDATE.nii.gz'],['Y2/POSTERIOR_AIR.nii.gz','Y2/POSTERIOR_CAUDATE.nii.gz']]
        dictionary_of_session_list={'AIR':['Y1/POSTERIOR_AIR.nii.gz','Y2/POSTERIOR_AIR.nii.gz'], 'CAUDATE':['Y1/POSTERIOR_CAUDATE.nii.gz','Y2/POSTERIOR_CAUDATE.nii.gz']}
    """
    from os.path import basename
    dictionary_of_session_list = {}
    assert not dg_list_list is None, "Input must be a list, not None"
    assert isinstance(dg_list_list, list), "Input must be a list, not {0}".format(type(postList))

    # Do the firt session for initialization
    first_session = dg_list_list[0]
    for postFileName in first_session:
        key = basename(postFileName).replace('POSTERIOR_', '').replace('.nii.gz', '')
        dictionary_of_session_list[key] = [postFileName]

    ## Now do the rest!
    for one_session_list in dg_list_list[1:]:
        for postFileName in one_session_list:
            key = basename(postFileName).replace('POSTERIOR_', '').replace('.nii.gz', '')
            assert key in list(dictionary_of_session_list.keys()), "All session list must have the same key values"
            dictionary_of_session_list[key].append(postFileName)
    print(dictionary_of_session_list)
    return dictionary_of_session_list


def GetOnePosteriorImageFromDictionaryFunction(postDict, key):
    return postDict[key]



def AccumulateLikeTissuePosteriors(posteriorImages):
    import os
    import sys
    import SimpleITK as sitk
    ## Now clean up the posteriors based on anatomical knowlege.
    ## sometimes the posteriors are not relevant for priors
    ## due to anomolies around the edges.

    load_images_list = dict()
    for full_pathname in posteriorImages:
        base_name = os.path.basename(full_pathname)
        load_images_list[base_name] = sitk.ReadImage(full_pathname)
    GM_ACCUM = [
        'POSTERIOR_SURFGM.nii.gz',
        'POSTERIOR_BASAL.nii.gz',
        'POSTERIOR_THALAMUS.nii.gz',
        'POSTERIOR_HIPPOCAMPUS.nii.gz',
        'POSTERIOR_CRBLGM.nii.gz',
    ]
    WM_ACCUM = [
        'POSTERIOR_CRBLWM.nii.gz',
        'POSTERIOR_WM.nii.gz'
    ]
    CSF_ACCUM = [
        'POSTERIOR_CSF.nii.gz',
    ]
    VB_ACCUM = [
        'POSTERIOR_VB.nii.gz',
    ]
    GLOBUS_ACCUM = [
        'POSTERIOR_GLOBUS.nii.gz',
    ]
    BACKGROUND_ACCUM = [
        'POSTERIOR_AIR.nii.gz',
        'POSTERIOR_NOTCSF.nii.gz',
        'POSTERIOR_NOTGM.nii.gz',
        'POSTERIOR_NOTVB.nii.gz',
        'POSTERIOR_NOTWM.nii.gz',
    ]
    ## The next 2 items MUST be syncronized
    AccumulatePriorsNames = ['POSTERIOR_GM_TOTAL.nii.gz', 'POSTERIOR_WM_TOTAL.nii.gz',
                             'POSTERIOR_CSF_TOTAL.nii.gz', 'POSTERIOR_VB_TOTAL.nii.gz',
                             'POSTERIOR_GLOBUS_TOTAL.nii.gz', 'POSTERIOR_BACKGROUND_TOTAL.nii.gz']
    ForcedOrderingLists = [GM_ACCUM, WM_ACCUM, CSF_ACCUM, VB_ACCUM, GLOBUS_ACCUM, BACKGROUND_ACCUM]
    AccumulatePriorsList = list()
    for index in range(0, len(ForcedOrderingLists)):
        outname = AccumulatePriorsNames[index]
        inlist = ForcedOrderingLists[index]
        accum_image = load_images_list[inlist[0]]  # copy first image
        for curr_image in range(1, len(inlist)):
            accum_image = accum_image + load_images_list[inlist[curr_image]]
        sitk.WriteImage(accum_image, outname)
        AccumulatePriorsList.append(os.path.realpath(outname))
    print(("HACK \n\n\n\n\n\n\n HACK \n\n\n: {APL}\n".format(APL=AccumulatePriorsList)))
    print((": {APN}\n".format(APN=AccumulatePriorsNames)))
    return AccumulatePriorsList, AccumulatePriorsNames


def mkdir_p(path):
    """ Safely make a new directory, checking if it already exists"""
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def recursive_dir_rm(path):
    """ Force recursive remove of directory """
    if os.path.exists(path):
        shutil.rmtree(path)
    return


def make_dummy_file(fn):
    """This function just makes a file with the correct name and time stamp"""
    import time
    mkdir_p(os.path.dirname(fn))
    ff = open(fn, 'w')
    ff.write("DummyFile with Proper time stamp")
    time.sleep(1)  # 1 second
    ff.close()
