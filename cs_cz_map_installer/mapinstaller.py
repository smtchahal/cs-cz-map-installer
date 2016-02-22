"""
This is the core module of cs_cz_map_installer. It contains all the functions
needed for checking and installing maps into game directory, plus various helper
functions
"""

import sys
import os
import string
import hashlib
import shutil
import tempfile
import logging

LOGGING_FORMAT = ("[%(asctime)s] %(levelname)s "
                "[%(name)s.%(funcName)s:%(lineno)d] %(message)s")
try:
    logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT, filemode='a',
                        filename='mapinstaller.log')
    logger = logging.getLogger(__name__)
except PermissionError:
    logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)
    logger = logging.getLogger(__name__)
    logger.warning("Don't have write permission in current"
                    " directory, logging to stderr instead")

class SameDirectoryError(OSError):
    """Raised when game_path and map_path are the same directory"""

class InvalidGameDirectoryError(Exception):
    """Raised when given game directory is found to be invalid"""

class InvalidMapDirectoryError(Exception):
    """Raised when given map directory is found to be invalid"""

def sha1sum(filename, buf=65536):
    """Calculate the SHA-1 checksum of a file using a specific buffer
    size so as to avoid placing the whole file into RAM.

    Args:
        filename: The file to calculate the checksum of
        buf: The buffer size to use in bytes (default: 65536)

    Returns:
        The corresponding SHA-1 checksum
    """

    sha1 = hashlib.sha1()
    with open(filename, 'rb') as f:
        while True:
            data = f.read(buf)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()

def install_map(map_path, game_path, game_type, replace=False):
    """
    Install map specified by map_path into game directory specified by
    game_path, assuming the game type specified by game_type.

    Args:
        map_path (str): the map directory
        game_path (str): the game directory (containing either of 'cstrike' or
                        'czero')
        game_type (str): the type of game; usually either of 'cstrike' or 'czero'
        replace (bool): whether to replace files in game_path of the same name
                        as in map_path (default: False)

    Raises:
        SameDirectoryError: if map_path and game_path refer to the same
        directory
        InvalidGameDirectoryError: if game_path does not contain a directory
        with its name equal to game_type
    """
    map_path = os.path.realpath(map_path)
    game_path = os.path.realpath(game_path)
    if map_path == game_path:
        raise SameDirectoryError("'{}' and '{}' are the same directories"
            .format(map_path, game_path))

    if game_type not in ls_dirs(game_path):
        raise InvalidGameDirectoryError(("'{}' is not a valid {} installation"
            "(directory {} not found)").format(game_path, game_type,
            os.path.join(game_path, game_type)))

    if game_type in ls_dirs(map_path):
        if 'maps' not in ls_dirs(os.path.join(map_path, game_type)):
            raise InvalidMapDirectoryError(("'{}' is not a valid map directory"
                " (directory '{}' not found").format(map_path,
                    os.path.join(map_path, 'maps')))
        # Nothing to be done, map directory is "perfect"
        copy_map_to_game(map_path, game_path, game_type, replace=replace)

    elif 'maps' in ls_dirs(map_path):
        logger.info('Found "maps" inside')
        with tempfile.TemporaryDirectory() as tempdir:
            logger.info('Created temporary directory {}'.format(tempdir))
            map_path_new = os.path.join(tempdir, game_type)
            logger.info('TEMP: Copying {} to {}'.format(map_path, map_path_new))
            shutil.copytree(map_path, map_path_new)
            copy_map_to_game(tempdir, game_path, game_type, replace=replace)
            logger.info('Removing temporary directory {}'.format(tempdir))
    else:
        logger.info('Inside else')
        found = False
        for filename in ls_files(map_path):
            if filename.endswith('.bsp'):
                logger.info('Found .bsp file')
                found = True
                break
        if not found:
            raise InvalidMapDirectoryError(("'{}' is not a valid {}"
                " installation (directory {} not found)").format(game_path,
                                                                game_type,
                                        os.path.join(game_path, game_type)))
        logger.info('map_path = ' + map_path)
        with tempfile.TemporaryDirectory() as tempdir:
            logger.info('Created temporary directory {}'.format(tempdir))
            os.makedirs(os.path.join(tempdir, game_type), exist_ok=True)
            map_path_new = os.path.join(tempdir, game_type, 'maps')
            logger.info('TEMP: Copying {} to {}'.format(map_path, map_path_new))
            shutil.copytree(map_path, map_path_new)
            copy_map_to_game(tempdir, game_path, game_type, replace=replace)
            logger.info('Removing temporary directory {}'.format(tempdir))

def copy_map_to_game(map_path, game_path, game_type, replace=False):
    """
    Copy files in map_path into game_path recursively, assuming game
    type specified by game_type.

    Args:
        map_path (str): the map directory (e.g. C:\\my_maps\\de_dust_cz)
                        containing directory with name game_type
        game_path (str): the game directory
                        (e.g. C:\\Program Files (x86)\\Condition Zero)
                        containing directory with name game_type
        game_type (str): the game type (usually either of 'czero' or 'cstrike')
        replace (bool): whether to replace files in game_path of the same name
                        as in map_path (default: False)
    """
    logger.info('About to go walk inside {}'.format(os.path.join(map_path,
                                                                game_type)))
    for dirpath, dirnames, filenames in os.walk(os.path.join(map_path,
                                                            game_type)):
        relpath = dirpath[len(map_path)+1:]
        dirpath2 = os.path.join(game_path, relpath)

        if not os.path.isdir(dirpath2):
            logger.warning('Directory {} does not exist, creating'
                            .format(dirpath2))
            os.makedirs(dirpath2)
        for filename in filenames:
            fsrc = os.path.join(dirpath, filename)
            fdst = os.path.join(dirpath2, filename)
            if os.path.isfile(fdst) and not replace:
                logger.info('SKIPPED Copying {} to {}'.format(fsrc, fdst))
                continue
            logger.info('Copying {} to {}'.format(fsrc, fdst))
            shutil.copy2(fsrc, fdst)
    logger.info('Finished copying')

def compare_dirs(map_path, game_path, game_type):
    """
    Compare map_path and game_path recursively, to see if there exist
    different files with the same name in game_path as in map_path.
    Return a tuple containing full path of the first differing files
    found in map_path and game_path, respectively.

    Args:
        map_path (str): the map directory
        game_path (str): the game directory
        game_type (str): the game type (usually either of 'czero' or 'cstrike')

    Returns:
        a tuple containing full path to the first differing files found
        in map_path and game_path, respectively; None if none are found
    """
    if os.path.realpath(map_path) == os.path.realpath(game_path):
        raise SameDirectoryError("'{}' and '{}' are the same directories"
            .format(map_path, game_path))
    for dirpath, dirnames, filenames in os.walk(os.path.join(map_path,
                                                                game_type)):
        relpath = dirpath[len(map_path)+1:]
        dirpath2 = os.path.join(game_path, relpath)

        for filename1 in filenames:
            filenames2 = ls_files(dirpath2)
            if filenames2 is None:
                break
            for filename2 in filenames2:
                file1 = os.path.join(dirpath, filename1)
                file2 = os.path.join(dirpath2, filename2)
                if (filename1 == filename2 and
                    sha1sum(file1) != sha1sum(file2)):
                    return (file1, file2)
    return None

def find_dir(name, path):
    """
    Find the first directory with name found in path.

    Args:
        name (str): the name of the directory to find
        path (str): the path in which to search

    Returns:
        the first directory with name found in path, None if not found
    """
    for root, dirs, files in os.walk(path):
        if name in dirs:
            return os.path.join(root, name)
    return None

def ls_dirs(path):
    """
    List all directories in path.

    Args:
        path (str): the path in which to search

    Returns:
        a set containing all directories in path, None if path is non-existent
    """

    for dirpath, dirnames, filenames in os.walk(path):
        return set(dirnames)
    return None

def ls_files(path):
    """
    List all files in path.

    Args:
        path (str): the path in which to search

    Returns:
        a set containing all files in path, None if path is non-existent
    """
    for dirpath, dirnames, filenames in os.walk(path):
        return set(filenames)
    return None

def get_game_path(paths, games=('czero', 'cstrike')):
    """
    Attempt to find an appropriate Counter Strike/Counter Strike:Condition Zero
    path given a list of paths and valid names, return None on failure.

    Args:
        paths (tuple): A tuple containing all the paths to search in
        games (tuple): A tuple containing all the games to match against
                        (default: ('czero', 'cstrike'))

    Returns:
        full path to the game directory if found, None otherwise
    """
    for path in paths:
        if os.path.isdir(path):
            for game in games:
                find_res = find_dir(game, path)
                if find_res:
                    return os.path.dirname(find_res)
    return None

def get_win_drives():
    """
    Return a list of available Windows drives (as in ['C', 'D', 'E']), the first
    one being the system drive (if found using os.getenv('SystemDrive')) in
    alphabetical order.

    Returns:
        the list of available Windows drives, an empty list if none are found
    """
    drives = []
    if os.getenv('SystemDrive'):
        drives.append(os.getenv('SystemDrive'))
    for drive in string.ascii_uppercase:
        if os.path.isdir(drive + ':\\') and drive not in drives:
            drives.append(drive)
    return drives
