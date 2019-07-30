import pandas as pd
import re
import pprint
import uuid
from bqapi import *
from bqapi.util import save_blob
from lxml import etree as ET

CSV_PATH = './HCPMetadata.csv'
BASE_FILE_PATH = '/cluster/brain/connectome_disks'
BISQUE_ROOT_URL = 'https://bisque.ece.ucsb.edu'
bq_session = BQSession().init_local('username', 'password', bisque_root=BISQUE_ROOT_URL, create_mex=True)


failed_files = []

def createCSVTags(path):
    #regex to get subject ID
    m = re.search('\d{6}', path)
    subject = m.group(0) if m else None
    if subject is None:
        return []

    #using pandas to read csv, and get the entire row for that subjectid
    data = pd.read_csv(CSV_PATH)
    slice = data.loc[data['Subject'] == int(subject)]
    slice = slice.to_dict()
    #print(slice)
    returnList = []
    for key, value in slice.iteritems():
        returnList.append((key, value))
    return returnList

# TODO: this function should take in a file path, parse it, and return a list of tuples containing all tags that should be added to this file
def createTags(filePath):
    tagList = []
    #always append filepath
    tagList.append(('path', filePath))

    #regex to find subject id, insert it
    m = re.search('\d{6}', filePath)
    subject = m.group(0) if m else None
    if subject is not None:
        tagList.append(('subjectID', subject))

    allTags = [ ("File type","NIFTY file","nii"),
                ("File type","GIFTY file","gii"),
                ("File type","text file","txt"),
                ("File type","fs","png"),
		("File type","fs","label"),
                ("File type","fs","stats"),
                ("File type","fs","spec"),
                ("File type","Chemical table format file","ctab"),
                ("File type","High resolution structural data file","mgz file","mgz"),
                ("File type","Matlab file","mat"),
                ("File type","fs","log"),
                ("File type","non-specific backup file","bak"),
                ("File type","Corel graphic file","crv file","crv"),
                ("File type","fs","touch"),
                ("File type","Freesurfer ribbon file","ribbon"),
                ("Image space","MNI Nonlinear","MNINonLinear"),
                ("Image space","MNI Nonlinear file spatially downsampled to a 32k mesh","fsaverage_LR32k"),
                ("Image type","T1-Weight-Image","T1w"),
                ("Image type","T1 weight Image","T1"),
                ("Image type","T2 weight Image","T2w"),
                ("Image type","T2 weight Image","T2"),
                ("Release-notes","release notes","release-notes"),
                ("MRI process status","fs","unprocessed"),
                ("MRI process status","preprocessed","MNINonLinear"),
                ("MRI process status","preprocessed","T1w"),
                ("MRI type","resting state functional","rfMRI"),
                ("MRI type","task-evoked functional","tfMRI"),
                ("MRI type","diffusion","dMRI"),
                ("Data type","timeseries fMRI data","dtseries"),
                ("Data type","dense connectivity matrix data","dconn"),
                ("Data type","label designations","dlabel"),
                ("Data type","scalar grayordinate data","dscalar"),
                ("Atlas","fs","aparc"),
                ("Atlas","fs","aparc_a2009s"),
                ("Image type","fs","aparc"),
                ("Image type","fs","aparc_a2009s"),
                ("Image type","fs","wmparc"),
                ("Distortion type","fs","ArealDistortion_FS"),
                ("Distortion type","fs","ArealDistortion_MSMALL"),
                ("Distortion type","fs","ArealDistortion_MSMALL"),
                ("surface registration","164k freesurfer mesh ","164k_fs_LR"),
                ("surface registration","32k freesurfer mesh ","32k_fs_LR"),
                ("Image type","fs","shape"),
                ("Image type","fs","label"),
                ("Image type","fs","func"),
                ("Image type","fs","surf"),
                ("Workbench-readable file","fs","wb"),
                ("Image type","fs","native"),
                ("Data type","results for rfMRI and tfMRI scans","results"),
                ("Scan Position","left","L"),
                ("Scan Position","right","R"),
                ("Task","rest","REST1"),
                ("Task","rest","REST2"),
                ("Task","emotion processing","EMOTION"),
                ("Task","gambling","GAMBLING"),
                ("Task","language","LANGUAGE"),
                ("Task","motor","MOTOR"),
                ("Task","relational processing","RELATIONAL"),
                ("Task","social cognition","SOCIAL"),
                ("Task","working memory","WM"),
                ("Phase Encoding","rl","RL"),
                ("Phase Encoding","lr","LR"),
                ("Image type","region of interest","ROIs"),
                ("File type","fs","xfms"),
                ("Spatial Alignment","acpc","acpc"),
                ("Data type","diffusion data directory","Diffusion"),
                ("Data type","diffusion weighting (b-value) for each volume","bvals"),
                ("Data type","contains the diffusion direction (b-vector) for each volume","bvecs"),
                ("Data type","preprocessed diffusion time series file","data"),
                ("Data type","brain mask in diffusion space","nodif_brain_mask"),
                ("Tissue type", "midthickness","midthickness"),
                ("Tissue type","pial","pial"),
                ("Tissue type","white matter","white"),
                ("Tissue type","fs","wmparc"),
                ("Tissue type", "corr thickness","corrThickness"),
                ("Tissue type", "curvature of the brain","curvature"),
                ("Tissue type", "flat of the brain","flat"),
                ("Tissue type", "inflated","inflated"),
                ("Tissue type", "very inflated","very_inflated"),
                ("Tissue type", "thickness","thickness"),
                ]
                #allTags should be list of tuples containing tag fields, tag values, and what tag values will be in file names and paths
                #EXAMPLE: (tag field, tag value, file path string indicating value)
    pathAsList = filePath.split("/")
    fileName = pathAsList.pop()
    fileName = fileName.replace("."," ")
#    fileName = fileName.replace("_"," ")
    fileName = fileName.split(" ")
    #print(fileName)
    for possTag in pathAsList:
        for tag in allTags:
            if possTag == tag[2]:
                tagList.append(tag[0:2])
    #fileName = fileName.split(".")
    for possTag in fileName:
        for tag in allTags:
            if possTag == tag[2]:
                tagList.append(tag[0:2])
    return(tagList)



def process_full_set(session, start_path):
    '''
        This function will upload files (including non-images) and add annotations to the image
        get relevant file paths
    '''
    file_list = []
    uri_list = []
    file_names = []
    for dirname, dirnames, filenames in os.walk(start_path):
        for filename in filenames:
            # find relevant images
            # TODO: Add a check for the file types / avoid certain types
            file_names.append(filename.split('.')[0])
            path = os.path.join(dirname, filename)
            path = path.replace('\\', '/')
            file_list.append(path)
	    if notFsFile(path):	
	         if isValidFile(path):
        	        r = save_blob(session, path)
                	if r is None:
                   	 print('Error uploading')
                        # r is a created metadata document in etree form
               		else:
                    		uri = r.get('uri')

                        #this line adds all the tags (by passing into createtags to get the tags, then passing the return into addtags)
                   		addTag(uri, path)

                   		uri_list.append(uri)
		   		print(uri) 
    return uri_list

   
#check if it is freesurfer files
def notFsFile(path):
    tags = createTags(path)
    valid = False
    Sum = 0
    Sum1 = 0
    Sum2 = 0
    for key, val in tags:
		if val == "T1-Weight-Image":
			Sum1 = 1
    for key, val in tags: 
		if val == "NIFTY file":
			Sum2 = 1
    Sum = Sum1+Sum2
    if Sum == 2:
	valid = True
    return(valid)	
	

#tags is a list of pairs, in (name, value) format
def addTag(uri, path):
    image = bq_session.load(uri)
    #error checking on image, if it failed, add to failed files list and print error
    if image is None:
        failed_files.append(uri)
        print(uri + ' failed to load')
        return
    #load metadata and add fields
    print(path)
    tags = createTags(path)
    csvTags = createCSVTags(path)



    image = bq_session.fetchxml(uri)
    modified = annotation_add(image, ann_name='uri', ann_value=str(uri), ann_type="annotation", add_if_exists=True)
    #unpacking tuple into key value form
    for key, val in tags:
        modified = annotation_add(image, ann_name=key, ann_value=str(val), ann_type="annotation", add_if_exists=True)
    for key, val in csvTags:
        modified = annotation_add(image, ann_name=key, ann_value=str(val), ann_type="annotation", add_if_exists=True)
    if len(modified)>0:
        bq_session.postxml(uri, image, method='PUT')
	print(image)
    #finishing session/closing


def annotation_add(resource, ann='tag', ann_name=None, ann_value=None, ann_type=None, add_if_exists=False):
    modified = []
    if ann_name is not None and ann_value is not None:
        xpath = '//%s[@name="%s" and @value="%s"]'%(ann, ann_name, ann_value)
        if ann_type is not None:
            xpath = xpath.replace(']', ' and @type="%s"]'%ann_type)
        anns = resource.xpath(xpath)
        if len(anns) < 1 or add_if_exists is True:
                g = etree.SubElement(resource, ann, name=ann_name, value=ann_value)
                if ann_type is not None:
                    g.set('type', ann_type)
                modified.append({'g': g})
    return modified


def isValidFile(path):
    statinfo = os.stat(path)
    size = statinfo.st_size
    return (size != 0)

def createTagsTest():
    li1 = createTags('/100206/MNINonLinear/Results/rfMRI_REST2_LR/rfMRI_REST2_LR.L.native.func.gii')
    li2 = createTags('/100206/T1w/Diffusion/data.nii.gz')
    li3 = createTags('/100206/T1w/Results/tfMRI_GAMBLING_RL/PhaseOne_gdc_dc.nii.gz')

    pprint.pprint(li1)
    pprint.pprint(li2)
    pprint.pprint(li3)

def createCSVTagsTest():
    li1 = createCSVTags('/100206/MNINonLinear/Results/rfMRI_REST2_LR/rfMRI_REST2_LR.L.native.func.gii')
    li2 = createCSVTags('/100206/T1w/Diffusion/data.nii.gz')
    li3 = createCSVTags('/100206/T1w/Results/tfMRI_GAMBLING_RL/PhaseOne_gdc_dc.nii.gz')
    pprint.pprint(li1)
    pprint.pprint(li2)
    pprint.pprint(li3)

#createTagsTest()  
#createCSVTagsTest()

process_full_set(bq_session, BASE_FILE_PATH)
