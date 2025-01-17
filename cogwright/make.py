#!python
#-- cogwright.make

"""
"""

import os
import shutil
import sys

from datetime import datetime
from pathlib import Path
from ftplib import FTP

import tarfile
from zipfile import ZipFile
from getpass import getpass

#----------------------------------------------------------------------#

###
def collect_package_data( path_package ) :
    """"""
    root_path = Path( __file__ ).parents[0].resolve( ) / path_package
    package_data = list( )

    for root, _, _ in os.walk( str( root_path ) ) :
        package_data.append( str( Path( root ) / '*' ) )

    return package_data

def collect_manifest_data( path_manifest, path_exclude ) :
    """"""
    manifest_filepath = Path( __file__ ).parents[0].resolve( ) / path_manifest
    package_data = list( )

    # todo: read exclusion list first
    with open( manifest_filepath ) as f :
        for line in f :
            package_data.append( line )

    return package_data

def write_manifest( manifest_path ) :
    """"""
    pass

#----------------------------------------------------------------------#

def backup_payload( path_payload: Path ) :
    backup_time = datetime.now( )

    backup_time_str = backup_time.strftime( "%Y%m%d%H%M%S" )
    path_backup = path_payload.parents[1] / '__backup__' / backup_time_str / 'payload'
    while 1 :
        try :
            shutil.move( str( path_payload ), str( path_backup ) )
            print( "MOVE", str( path_payload ), str( path_backup ) )
            break
        except FileNotFoundError as e :
            # print(e)
            # raise e
            break

        except PermissionError as e :
            pass

#----------------------------------------------------------------------#

def authenticate_ftp( ) :
    """"""
    username = None
    pasword = None
    try :
        import __auth__

        username = __auth__.username
        password = __auth__.password
    except ImportError :
        username = input( "username:" )
        password = getpass( "password:" )
        #ToDo: save in __auth__.py file
    return username, password

#----------------------------------------------------------------------#

def archive_path( path_download: Path, path_archive ) -> Path :
    filename = None
    extension = None

    import __blueprint__ as blueprint
    print("path_archive", path_archive)

    if path_archive is not None :
        filepath_archive = Path( path_archive )
        filename = filepath_archive.name

    else:
        # select package -- [platform-specific]
        if sys.platform == "win32" :
            filename = blueprint.payload_filename_win

        elif sys.platform == "linux" or sys.platform == "linux2" :
            filename = blueprint.payload_filename_nix

        else :
            raise OSError( "Unsupported Platform: " + sys.platform )

        filepath_archive = Path( path_download ) / filename

    return filepath_archive, filename



def download_payload( path_download: Path, path_archive ) -> (Path, str) :
    print( "DOWNLOAD_payload", path_download )
    print( "PATH_ARCHIVE", path_archive)

    filepath_archive    = path_archive
    filename            = path_archive.name


    if not path_download.exists( ) :
        path_download.mkdir( )

    print("FILEPATH_ARCHIVE", filepath_archive)
    if not filepath_archive.exists( ) : # don't download if it's already there

        (username, password) = authenticate_ftp()
        # download from FTP
        # ToDo: support alternate download locations for people trapped behind company firewalls
        import __blueprint__ as blueprint
        url_ftp = blueprint.url_ftp
        with FTP( url_ftp ) as ftp :
            ftp.login( user=username, passwd=password )
            ftp.cwd( '/dist/' )

            with open( str( filepath_archive ), 'wb' ) as localfile :
                ftp.retrbinary( 'RETR ' + filename, localfile.write, 1024 )

    return filepath_archive.resolve()

def install_payload( path_localfile ) :
    pass

    # ToDo: store localfile in __file__ path ???

#----------------------------------------------------------------------#

def build_source( filepath_archive: Path,
                  path_download: Path,
                  path_payload: Path
                  ) :

    ### extract archive to source path
    import __blueprint__ as blueprint
    path_extract_tmp    = path_download / blueprint.extract_tmp_suffix
    path_extract        = path_download / blueprint.extract_suffix
    path_source         = blueprint.path_source

    extension           = filepath_archive.suffix

    if extension == '.zip' :
        ### https://stackoverflow.com/questions/3451111/unzipping-files-in-python
        with ZipFile( str( filepath_archive ), "r" ) as zip_ref :
            zip_ref.extractall( str( path_download ) )
    elif extension == '.gz' :
        with tarfile.open( str( filepath_archive ), "r:gz" ) as tar :
            print( "GZIP", path_download )
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tar, str(path_download))

    path_extract_tmp.rename( path_extract )
    shutil.move( str( path_extract ), str( path_source ) )

    ### create __version__.py
    version = blueprint.write_version_file(path_payload)
    print( "VERSION", version )

    ### create manifest, subtract excludelist

#----------------------------------------------------------------------#
