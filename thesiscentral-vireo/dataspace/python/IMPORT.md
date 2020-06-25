# Importing DataSpace Items

## Importing Thesis Central (Vireo) submissions into DataSpace (DSpace)
Thesis Central submissions are organized by academic departments.

## Preparing a local environment

### Installing `pipenv`

```
# For Python 3.x support:
pyenv local 3.8.3

# Or, for legacy support:
pyenv local 2.7.18

pip install pipenv
```

### Installing the Python package dependencies

#### 3.8.3

```
pipenv --python 2.7.18 shell
pipenv lock --pre
pipenv install
```

#### 2.7.18

```
cp Pipfile.legacy Pipfile
cp Pipfile.legacy.lock Pipfile
pipenv --python 2.7.18 shell
pipenv lock --pre
pipenv install
```

### Tunneling over SSH

In order to execute these scripts, one must first tunnel over SSH for copying
files using `scp`:

```bash
ssh -L 1234:dataspace.princeton.edu:22 $USER@epoxy.princeton.edu
```

...where `$USER` is an OIT service account used to access the production or QA
server environments for DSpace.

## Exporting from Thesis Central
Users must export Excel Spreadsheet after selecting a department from [Thesis Central](thesis-central.princeton.edu).

Please note that one must include the following columns in the export:

* ID
* Thesis Type
* Certificate Program
* Department
* Student name
* Student email
* Multi Author
* Institutional ID
* Submission date
* Advisors
* Document language
* Document title
* Status
* Primary document
* Approval date
* Event time

![alt text](./docs/thesis-central_screenshot_4.png)

One then exports both the `Excel Export (with Document URLs)`:

![alt text](./docs/thesis-central_screenshot_5.png)

...as well as the `DSpace Simple Archive`:

![alt text](./docs/thesis-central_screenshot_6.png)

Please download the Excel Export into `~/Download/thesis_central_export.xlsx`, 
and the DSpace Simple Archive into `~/Download/dspace_simple_archive.zip`.

## Applying Restrictions

One must then export the submission restrictions from the University Sharepoint
provided by the Office of the Registrar (please download the latest export from 
[Google Drive](https://drive.google.com/file/d/1yVsV5PG-WPtj-eV7lHGRbuj3sVUGdwZh/view?usp=sharing)).

Then, one must add an `ID` column to this exported spreadsheet:

![alt text](./docs/thesis-central_screenshot_1.png)
![alt text](./docs/thesis-central_screenshot_2.png)

## Building DSpace Submission Information Packages (SIPs)

Please note that this assumes that you have downloaded the Thesis Central 
departmental Excel Spreadsheet into `~/Download/thesis_central_export.xlsx`, and
the departmental DSpace Simple Archive into `~/Download/dspace_simple_archive.zip`.

### bash

```bash
export department="English"
mkdir export/$department
cp ~/Download/thesis_central_export.xlsx export/$department/ExcelExport.xlsx
cp ~/Download/dspace_simple_archive.zip export/$department/
pipenv run prepare-to-dataspace export/$department
```

### tcsh

```tcsh
set department="English"
mkdir export/$department
cp ~/Download/thesis_central_export.xlsx export/$department/ExcelExport.xlsx
cp ~/Download/dspace_simple_archive.zip export/$department/
pipenv run prepare-to-dataspace export/$department
```

### Multi-Author Submissions

```bash
cd export/Multi-Author
check_all_approved

combine_all_approved
check_after_combine
```

#### Transfer the SIPs to the server

##### bash

```bash
export department="Multi-Author"
(cd export; tar cfz $department.tgz ./$department)
scp -P 1234 export/$department.tgz $USER@dataspace.princeton.edu:/var/scratch/thesis-central/$department.tgz
ssh $USER@dataspace.princeton.edu chmod o+r /var/scratch/thesis-central/$department.tgz
```

##### tcsh

```tcsh
set department="Multi-Author"
(cd export; tar cfz $department.tgz ./$department)
scp -P 1234 export/$department.tgz $USER@dataspace.princeton.edu:/var/scratch/thesis-central/$department.tgz
ssh $USER@dataspace.princeton.edu chmod o+r /var/scratch/thesis-central/$department.tgz
```

## Import to DataSpace

From the DataSpace server environment, please invoke the following:

### tcsh

```tcsh
ssh -J $USER@epoxy.princeton.edu $USER@dataspace.princeton.edu
su - root
su - dspace
cd ~thesiscentral-vireo/dataspace/import
./unwrap

# Just cut and paste the derived .tgz file from the prompt
# Test access for the directories at https://dataspace.princeton.edu/www/thesis_central/

# Then import to DSpace using the following:
./import
```
