# Princeton Plasma Physics Laboratory (PPPL) Collection Management

Python administration scripts for managing the [Princeton Plasma Physics Laboratory Collection](https://dataspace.princeton.edu/jspui/handle/88435/dsp01pz50gz45g) in [DataSpace](https://dataspace.princeton.edu/jspui/).

## Getting Started

### Install and Configure the AWS CLI

```
python -m pip install --user awscli
```

Please ensure that the following configuration files are in place for AWS:

```
$ cat $HOME/.aws/credentials
[default]
aws_access_key_id = [KEY_ID]
aws_secret_access_key = [SECRET_ACCESS_KEY]
aws_region = us-east-1
```

```
$ cat $HOME/.aws/config
[default]
```

Alternatively, should access fail, please explicitly declare the BASH
environment variables:

```
export AWS_ACCESS_KEY_ID=[KEY_ID]
export AWS_SECRET_ACCESS_KEY=[SECRET_ACCESS_KEY]
export AWS_DEFAULT_REGION=us-east-1
```

### Clone the repository

```
$ cd pulibrary-src/
$ git clone https://github.com/pulibrary/dspace-python.git
$ cd dspace-python/pppl
```

## Pulling Submission Information Packages (SIPs) from the PPPL

```
python dataspace_import.py $DSPACE_HOME $DSPACE_EPERSON $DSPACE_AWS_S3
```
