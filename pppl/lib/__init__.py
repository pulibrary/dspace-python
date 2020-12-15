import os
import sys
import shutil
import logging
import argparse
from pathlib import Path
import pdb
import boto3
import re

LOGLEVEL = "DEBUG"
SKIP = 'SKIP'
IMPORT = 'IMPORT'
DONE = 'DONE'
INTERNAL = 'INTERNAL'

class Package:
    def __init__(self, path):
        self.path = path

class PackageDirectory:

    def __init__(self, path, import_service):
        self._path = path
        self._import_service = import_service
        self.logger = import_service.logger

        self._files = os.listdir(self._path)
        self._packages = self.parse_files()

    def isnewpackage(package_path):
        return ImportService.ispackagepath(package_path) and not self._import_service.isarchived(package_path)

    def parse_files(self):
        packages = []

        for s3_file in self._files:
            s3_file_path = pathlib.Path(s3_file)

        if self.isnewpackage(s3_file_path):
            package = Package(s3_file_path)
            packages.append(package)

        self._packages = packages
        return self._packages

    def ingest(self):
        status = True

        for package in self._packages:
            imported = self._import_service.ingest(package)
            if imported:
                self._import_service.batch_size += 1
            else:
                status = False

            # self._import_service.logger.info("Importing {}".format(package.path))
            # _import(self._import_service.s3_mirror, self._import_service.log, import_service.eperson, package, import_service)
        return status

class ImportService:
    @classmethod
    def ispackagepath(cls, file_path):
        return file_path.suffix == '.tgz'

    def build_mapfile_path(self, archive_path):
        mapfile_name = "{}.mapfile".format(archive_path.name)
        path = Path(self._package_bucket.mount_point, 'imports', mapfile_name)

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

    def _execute(self, command, logfile):

        with open(logfile, "a+") as f:
            f.write('> ' + command + '\n')

        return_code = os.system('({}) >> {} 2>&1'.format(command, logfile))

        if 0 != return_code:
            error_message = '{} rc={}'.format(command, return_code)
            self.logger.error(error_message)

            with open(logfile, "a+") as f:
                f.write('error\n')

        return return_code

    def import_into_dspace(self, source_path, mapfile_path):

        cmd = self._dataspace_import_cmd(source_path, mapfile_path)
        # rc = _systm(s3_file, cmd, logfile)
        return_code = self._execute(command, logfile)
        imported = return_code == 0 and self.isarchived(s3_file_path)

        return imported

    def _unpack(self, package, logfile):
        try:
            segments = package.path.split('.')
            dirname = "{}/imports/{}".format(self._package_bucket.mount_point, segments[0])
            # This structure is required for DSpace imports
            item_dirname = "{}/{}".format(dirname, "item_000")

            if not os.path.isdir(dirname):
                os.makedirs(dirname)
                os.makedirs(item_dirname)
        except Exception as error:
            error_message = 'Failed to create the directory {}: {}'.format(dirname, str(error))
            self.logger.error(error_message)
            return

        cmd = 'cd {}; tar xvfz {}/{}; cd -'.format(item_dirname, s3_dir, s3_file)
        rc = self._execute(cmd, logfile)
        if 0 == rc:
            return Path(dirname)

    def ingest(self, package):
        imported = False
        unpacked_dir = None

        s3_file_path = Path(package.path)

        # Replace this with package.mapfile
        mapfile_path = self.build_mapfile_path(s3_file_path)
        if mapfile_path.exists():
            self.logger.info('Removing the empty mapfile {}'.format(mapfile_path))
            mapfile_path.unlink()

        # Replace this with package.logfile
        logfile = self._logfile(package.path)
        try:
            # decompressed_dir_path = _unpack(self.s3_mirror, s3_file, logfile)
            decompressed_dir_path = self._unpack(package, logfile)

            if decompressed_dir_path.exists():
                # cmd = self._dataspace_import_cmd(decompressed_dir_path, mapfile_path)

                # rc = _systm(s3_file, cmd, logfile)
                # success = rc == 0 and self.isarchived(s3_file_path)
                imported = self.import_into_dspace(decompressed_dir_path, mapfile_path)
        except:
            # This needs to be handled
            pdb.set_trace()
            pass

        success_state = 'SUCCESS' if imported else 'FAILURE'
        self.logger.info('Import status for {}: {}'.format(package, success_state))
        if not imported:
            self.logger.warn('Please check the logging entries in {}'.format(logfile))

        return imported

    def _logfile(self, tgz):
        """
        Generate the file path for the DSpace import log file given a file name

        Parameters
        ----------
        tgz : str
            The path to the file
        """

        return '{}/imports/{}.log'.format(self._package_bucket.mount_point, tgz)

    def configure_logging(self):
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

    def __init__(self, dspace_home, eperson, package_bucket):
        self.dspace_home = dspace_home
        # This attribute should be renamed
        # self.s3_mirror = s3_mirror
        # This should be removed
        # self.aws_s3_path = self.s3_mirror
        self.eperson = eperson

        self.log = '{}/log'.format(self._package_bucket.mount_point)
        self.batch_size = 0

        self._package_bucket = package_bucket

class PackageBucket:
    def configure_logging(self):
        logger_level = logging.DEBUG

        logger = logging.getLogger()
        logger.setLevel(logger_level)

        self.logger = logger
        return self.logger

    def __init__(self, mount_point):
        self.mount_point = Path(mount_point)

        self._client = boto3.client('s3')
        self._s3 = boto3.resource('s3')

        self.buckets = list(self._s3.buckets.all())

        self.logger = self.configure_logging()

    def download(self, overwrite=False):
        for bucket in self.buckets:
            mounted_bucket_path = Path(self.mount_point, bucket.name)
            if not mounted_bucket_path.is_dir():
                mounted_bucket_path.mkdir()

            s3_resources = list(bucket.objects.all())
            sorted_s3_resources = sorted(s3_resources, key=lambda s3_resource: s3_resource.key)

            for s3_resource in sorted_s3_resources:
                file_path = Path(self.mount_point, bucket.name, s3_resource.key)
                s3_resource_summary = s3_resource.get()

                if s3_resource_summary['ContentType'] == 'application/x-directory':
                    dir_name = s3_resource.key
                    local_path = Path(self.mount_point, bucket.name, dir_name)

                    if not local_path.is_dir():
                        local_path.mkdir()
                elif not file_path.is_file() or overwrite:
                    file_path_value = str(file_path)
                    api_object = s3_resource.Object()
                    try:
                        api_object.download_file(file_path_value)
                    except Exception as download_error:
                        error_message = "Failed to download the AWS S3 resource {}: {}".format(s3_resource.key, download_error)
                        self.logger.error(error_message)

if __name__=="__main__":

    DSPACE_HOME = sys.argv[1]
    SUBMITTER = sys.argv[2]
    S3_MIRROR = sys.argv[3]

    aws_bucket = PackageBucket(S3_MIRROR)
    aws_bucket.download()

    import_service = ImportService(DSPACE_HOME, SUBMITTER, aws_bucket)
    import_service.configure_logging()

    logging.info('SETUP local-bucket-mirror:  {}'.format(import_service._package_bucket.mount_point))
    logging.info('SETUP log-directory:  {}'.format(import_service.log))
    logging.info('SETUP submitter:  {}'.format(import_service.eperson))

    # exit_code = _work_sips(import_service)

    package_dir = PackageDirectory(aws_bucket.mount_point, import_service)
    exit_code = package_dir.ingest()

    if exit_code != 0:
        import_service.logger.error('Failed to import {} packages into DSpace.'.format(s3_file_batch_size))
        sys.exit(exit_code)

    import_service.logger.info('SUCCESS all packages imported')
    sys.exit(0)
