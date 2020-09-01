import os
import sys
import shutil
import logging
import argparse

if len(sys.argv) < 4:
    raise Exception('Usage: dataspace_import.py $DSPACE_HOME $DSPACE_EPERSON $S3_PATH')

DSPACE_HOME = sys.argv[1]
SUBMITTER = sys.argv[2]
S3_MIRROR = sys.argv[3]

LOGLEVEL = "DEBUG"
SKIP = 'SKIP'
IMPORT = 'IMPORT'
DONE = 'DONE'
INTERNAL = 'INTERNAL'

s3_file_batch_size = 0
_nerror = 0

def _error(msg):
    """
    Log a message for the error log

    """

    global _nerror
    _nerror = _nerror + 1
    logging.error(msg)

    return None

def _info(pre, msg):
    """
    Log a message for the info log

    """

    logging.info('{}: {}'.format(pre, msg))

    return None

def _debug(pre, msg):
    """
    Log a message for the debugging log

    """
    logging.debug('{}: {}'.format(pre, msg))

    return None

def _mapfile(tgz):
    """
    Generate the file path for the DSpace import mapfile given a file name

    Parameters
    ----------
    tgz : str
        The path to the file

    """
    return '{}/imports/{}.mapfile'.format(S3_MIRROR, tgz)


def _check_internal(file_name, s3_files):
    """
    Determines whether or not to import a file into DSpace given its file name.

    Parameters
    ----------
    file_name : str
        The path to the file
    s3_files : list
        An unused parameter (this should be removed)

    Returns
    -------
    str
        The status of the file

    """

    output = None
    if file_name.endswith('.mapfile') or file_name.endswith('log') or file_name == 'imports':
        output = INTERNAL
    else:
        mapfile_status = _check_mapfile(file_name)
        if mapfile_status:
            output = INTERNAL
        else:
            output = IMPORT

    return output

def _systm(s3_file, cmd, logfile):
    """
    Execute a command using the BASH

    Parameters
    ----------
    s3_file : str
        The path to the file
    cmd : str
        The command being executed in the shell
    logfile : str
        The path to the logging file

    Returns
    -------
    int
        The return code of the command

    """
    logging.info(cmd)
    with open(logfile,"a+") as f: f.write('> ' + cmd + '\n')
    rc = os.system('({}) >> {} 2>&1'.format(cmd, logfile))

    if 0 != rc:
        msg = '{} rc={}'.format(cmd, rc)
        _error(msg)
        with open(logfile,"a+") as f: f.write('ERROR\n')
    return rc

def _unpack(s3_dir, s3_file, logfile):
    """
    Decompress the GZipped TAR into a directory

    Parameters
    ----------
    s3_dir : str
        The directory path for the S3 synchronization
    s3_file : str
        The TAR file from the S3 Bucket
    logfile : str
        The path to to the log file

    Returns
    -------
    str
        The name of the directory where the TAR has been decompressed
    """
    try:
        segments = s3_file.split('.')

        dirname = "{}/imports/{}/{}".format(S3_MIRROR, segments[0], "item_000")
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
    except Exception as error:
        logging.error(str(error))
        return _error('could not create {}'.format(dirname))

    cmd = 'cd {}; tar xvfz {}/{}'.format(dirname, s3_dir, s3_file)
    rc = _systm(s3_file, cmd, logfile)
    if 0 == rc:
        import_dirname = "{}/imports/{}".format(S3_MIRROR, segments[0])
        return import_dirname
    else:
        return None


def _check_mapfile(s3_file):
    """
    Check the mapfile for a file which has imported into DSpace

    Parameters
    ----------
    s3_file : str
        The directory path for the submission information package

    Returns
    ----------
    bool

    """
    mapfile = _mapfile(s3_file)
    ok = (os.path.isfile(mapfile) and 0 < os.path.getsize(mapfile))

    if not ok:
        _error('broken mapfile for {}'.format(s3_file))

    return ok

# This is no longer used
def _cleanup_dir(dirname):
    dirname = str(dirname)

    if dirname:
        if os.path.exists(dirname):
            shutil.rmtree(dirname)
            logging.info('rmtree ' + dirname)
        else:
            logging.error('directory "{}" does not exist'.format(dirname))


def _cleanup_file(fname):
    """
    Delete a file

    Parameters
    ----------
    fname : str
        The directory path for the S3 synchronization
    """

    if os.path.exists(fname):
        os.remove(fname)
        logging.info('rmfile ' + fname)

def _import(s3_mirror, log, submitter, s3_file, service):
    """
    Import a file into DSpace given the file path

    Parameters
    ----------
    s3_mirror : str
        The directory path for the S3 synchronization
    log : Object
        The system logger
    submitter: str
        Submitter account
    s3_file : str
        File path for the file in the S3 Bucket
    service : Object
        Importer service
    """

    success = False
    unpacked_dir = None
    mapfile = _mapfile(s3_file)

    if os.path.exists(mapfile):
        _cleanup_file(mapfile)

    try:
        logfile = service._logfile(s3_file)
        logging.info('logging {} import to {}'.format(s3_file, logfile))
        unpacked_dir = _unpack(service.s3_mirror, s3_file, logfile)

        if unpacked_dir:
            cmd = _dataspace_import_cmd(unpacked_dir, service.submitter, mapfile)
            rc = _systm(s3_file, cmd, logfile)
            success = rc == 0 and _check_mapfile(s3_file)
    except:
        pass

    success_state = 'SUCCESS' if success else 'FAILURE'
    logging.info('{} {}'.format(s3_file, success_state))
    if not success:
        logging.info('Please check the logging entries in {}'.format(logfile))

    logging.info('----')

def _work_sips(s3_mirror, log, submitter):
    """
    Imports the S3 data sets into a DSpace installation

    Parameters
    ----------
    s3_mirror : str
        The directory path for the S3 synchronization
    log : Foo
        The system logger
    submitter : str
        The e-mail address for the DSpace user importing the data sets

    """
    logging.info('SETUP local-bucket-mirror:  {}'.format(service.s3_mirror))
    logging.info('SETUP log-directory:  {}'.format(service.log))
    logging.info('SETUP submitter:  {}'.format(service.submitter))

    s3_files = os.listdir(service.s3_mirror)
    s3_file_batch_size = len(s3_files)
    for s3_file in s3_files:
        status = _check_internal(s3_file, s3_files)

        if (status != INTERNAL):
            _debug(s3_file, str(status))

            if (status == IMPORT):
                _import(service.s3_mirror, service.log, service.submitter, s3_file, service)

    return _nerror

class ImporterService:
    def _dataspace_import_cmd(sip_dir, submitter, mapfile, service):
        """
        Import a directory into DataSpace

        Parameters
        ----------
        sip_dir : str
            The directory path for the submission information package
        submitter : str
            The e-mail address of the submitter account in DSpace
        mapfile : str
            The file path to the DSpace import mapfile
        """

        import_cmd = '{}/bin/dspace import --add --workflow -notify  -e {} --mapfile {} -s {} '
        import_cmd = import_cmd.format(service.dspace_home, submitter, mapfile, sip_dir)

        return import_cmd

    def _logfile(tgz):
        """
        Generate the file path for the DSpace import log file given a file name

        Parameters
        ----------
        tgz : str
            The path to the file
        """

        return '{}/imports/{}.log'.format(self.s3_mirror, tgz)

    def configure_logging(self):
        if self.args.verbose > 1:
            logger_level = logging.DEBUG
        elif self.args.verbose == 1:
            logger_level = logging.INFO
        else:
            logger_level = logging.WARNING

        logger = logging.getLogger()
        logger.setLevel(logging_level)

        self.logger = logger
        return self.logger

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Import PPPL submission information packages into DataSpace.')

        parser.add_argument("-d", "--dspace-home", help="DSpace home directory")
        parser.add_argument("-e", "--eperson", help="DSpace EPerson e-mail account")
        parser.add_argument("-s", "--s3-mirror", help="Amazon Web Services S3 mirror directory")
        parser.add_argument("-v", "--verbose", help="Increase the verbosity of the logging", action="count")
        args = parser.parse_args()

        self.args = args
        return self.args

    def __init__(self, s3_mirror, eperson):
        self.s3_mirror = s3_mirror
        self.eperson = eperson
        self.log = '{}/log'.format(self.s3_mirror)

if __name__=="__main__": 
    service = ImporterService(s3_mirror)
    service.parse_args()
    service.configure_logging()

    s3_file_batch_size = 0
    _nerror = 0

    exit_code = _work_sips(service)
    if exit_code == 0:
        service.logging.info('SUCCESS all packages imported')
        sys.exit(0)
    else:
        _error('failed to import {} packages'.format(s3_file_batch_size))
        sys.exit(exit_code)
