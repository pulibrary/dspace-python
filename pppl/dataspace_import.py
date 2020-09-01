import os
import sys
import shutil
import logging
import argparse
import pathlib2 as pathlib
from pathlib2 import Path

import pdb

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
        dirname = "{}/imports/{}".format(S3_MIRROR, segments[0])
        # This structure is required for DSpace imports
        item_dirname = "{}/{}".format(dirname, "item_000")

        if not os.path.isdir(dirname):
            os.makedirs(dirname)
            os.makedirs(item_dirname)
    except Exception as error:
        logging.error(str(error))
        return _error('could not create {}'.format(dirname))

    cmd = 'cd {}; tar xvfz {}/{}; cd -'.format(item_dirname, s3_dir, s3_file)
    rc = _systm(s3_file, cmd, logfile)
    if 0 == rc:
        return Path(dirname)
    else:
        return None

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
    s3_file_path = Path(s3_file)

    mapfile_path = service.build_mapfile_path(s3_file_path)
    if mapfile_path.exists():
        service.logger.info('Removing the empty mapfile {}'.format(mapfile_path))
        mapfile_path.unlink()

    logfile = service._logfile(s3_file)
    try:
        decompressed_dir_path = _unpack(service.s3_mirror, s3_file, logfile)

        if decompressed_dir_path.exists():
            cmd = service._dataspace_import_cmd(decompressed_dir_path, mapfile_path)

            rc = _systm(s3_file, cmd, logfile)
            success = rc == 0 and service.isarchived(s3_file_path)
    except:
        pass

    success_state = 'SUCCESS' if success else 'FAILURE'
    service.logger.info('Import status for {}: {}'.format(s3_file, success_state))
    if not success:
        logging.info('Please check the logging entries in {}'.format(logfile))

    logging.info('----')

def _work_sips(service):
    """
    Imports the S3 data sets into a DSpace installation

    Parameters
    ----------
    s3_mirror : str
        The directory path for the S3 synchronization
    log : Logger
        The system logger
    submitter : str
        The e-mail address for the DSpace user importing the data sets

    """
    logging.info('SETUP local-bucket-mirror:  {}'.format(service.s3_mirror))
    logging.info('SETUP log-directory:  {}'.format(service.log))
    logging.info('SETUP submitter:  {}'.format(service.eperson))

    s3_files = os.listdir(service.s3_mirror)
    s3_file_batch_size = len(s3_files)
    for s3_file in s3_files:
        s3_file_path = pathlib.Path(s3_file)

        if (ImporterService.isarchivepath(s3_file_path) and not service.isarchived(s3_file_path)):
            service.logger.info("Importing {}".format(s3_file_path))
            _import(service.s3_mirror, service.log, service.eperson, s3_file, service)

    return _nerror

class ImporterService:
    # This needs to be refactored
    @classmethod
    def aws_s3_path(cls):
        return S3_MIRROR

    @classmethod
    def isarchivepath(cls, file_path):
        return file_path.suffix == '.tgz'

    def build_mapfile_path(self, archive_path):
        mapfile_name = "{}.mapfile".format(archive_path.name)
        path = Path(self.aws_s3_path, 'imports', mapfile_name)

        return path

    def isarchived(self, file_path):
        mapfile_path = self.build_mapfile_path(file_path)
        status = mapfile_path.exists() and mapfile_path.stat().st_size > 0

        return status

    def _dataspace_import_cmd(self, sip_dir, mapfile):
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

        import_cmd = '{}/bin/dspace import --add --workflow --eperson {} --mapfile {} --source {}'
        cmd = import_cmd.format(self.dspace_home, self.eperson, mapfile, sip_dir)
        self.logger.info(cmd)

        return cmd

    def _logfile(self, tgz):
        """
        Generate the file path for the DSpace import log file given a file name

        Parameters
        ----------
        tgz : str
            The path to the file
        """

        return '{}/imports/{}.log'.format(self.s3_mirror, tgz)

    def configure_logging(self):
        #if self.args.verbose > 1:
        #    logger_level = logging.DEBUG
        #elif self.args.verbose == 1:
        #    logger_level = logging.INFO
        #else:
        #    logger_level = logging.WARNING

        logger_level = logging.DEBUG

        logger = logging.getLogger()
        logger.setLevel(logger_level)

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

    def __init__(self, dspace_home, s3_mirror, eperson):
        self.dspace_home = dspace_home
        # This attribute should be renamed
        self.s3_mirror = s3_mirror
        self.aws_s3_path = self.s3_mirror
        self.eperson = eperson
        self.log = '{}/log'.format(self.s3_mirror)

if __name__=="__main__":
    service = ImporterService(DSPACE_HOME, S3_MIRROR, SUBMITTER)
    # service.parse_args()
    service.configure_logging()

    s3_file_batch_size = 0
    _nerror = 0

    exit_code = _work_sips(service)
    if exit_code == 0:
        service.logger.info('SUCCESS all packages imported')
        sys.exit(0)
    else:
        _error('failed to import {} packages'.format(s3_file_batch_size))
        sys.exit(exit_code)
