# Parsing and Extract Metadata of T1w images in HCP dataset, and Uploading the Images with Metadata into Bisque
Add annotation of T1w images in HCP dataset by parsing its absolute path to build metadata, and then upload the images with their metadata into Bisque.
***
## Using Steps
1. Log in to your Brain server account  
```
ssh username@brain.ece.ucsb.edu
```  
2. clone the repositroy to your account  
3. install the require libraries  
```
pip install pandas  
pip install re
pip install uuid
pip install bqapi
pip install lxml
```
4. edit #username# and #password# in UpLoadHCPfiles.py at line #11
```
bq_session = BQSession().init_local('#username#', '#password#', bisque_root=BISQUE_ROOT_URL, create_mex=True)
```  
5. Run the code
```
python UpLoadHCPfiles.py
```
## Explaination
line#8: his is the declaration of the path of .csv file
```
CSV_PATH = './HCPMetadata.csv'
```
line#9: this is the path of what directory you want to upload and here is the whole HCP dataset directory path in Brain server
```
BASE_FILE_PATH = '/cluster/brain/connectome_disks'
```
line#10: here is the Bisque root url which will add to the url of metadata and send to Bisque
```
BISQUE_ROOT_URL = 'https://bisque.ece.ucsb.edu'
```
