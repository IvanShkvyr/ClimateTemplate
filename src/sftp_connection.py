from ftplib import FTP
from paramiko import SSHException
import os

import pysftp


def connect_to_sftp(
                    host: str,
                    username: str,
                    password: str,
                    port: int
                    ) -> pysftp.Connection:
    """
    Connects to the SFTP server using the provided credentials and port.

    This function attempts to establish a connection to an SFTP server with the
    given host, username, password, and port. It also checks if the 'data'
    directory exists on the server, returning the connection object if
    successful, or None if the connection fails or the directory is not found.

    Args:
        host (str): The hostname or IP address of the SFTP server.
        username (str): The username used to authenticate to the server.
        password (str): The password used to authenticate to the server.
        port (int): The port number to connect to the SFTP server.

    Returns:
        pysftp.Connection: The connection object if successful, or None if the
            connection fails.
    """
    cnopts = pysftp.CnOpts()
    
    # NOTE: You should use the following block to explicitly load known host keys:
    #
    # Example:
    # cnopts.hostkeys.load(os.path.expanduser('~/.ssh/known_hosts'))
    #
    # This will load the host keys from your known_hosts file to verify the server's identity.
    # It is highly recommended to use host key verification for security purposes.
    
    # Disabling host key checking (not secure, use for testing only)
    cnopts.hostkeys = None

    try:
        # Establishing connection using context manager
        sftp = pysftp.Connection(
                                host=host,
                                username=username,
                                password=password,
                                port=port,
                                cnopts=cnopts
                                )
        print(f"Connected successfully to SFTP server on port {port}")
            
        # Checking if 'data' directory exists on the server
        try:
            files = sftp.listdir("data")
            print(f"Files in 'data' directory: {files}")
            # Returning the connection object
            return sftp

        except FileNotFoundError:
            print("Directory 'data' not found on the server.")
            return None

    except SSHException as e:
        print(f"Error connecting to SFTP server: {e}")
        return None

    except Exception as e:
        # Catching general exceptions for better diagnostics
        print(f"An unexpected error occurred: {e}")
        return None


def upload_directory(
                    sftp: pysftp.Connection,
                    source: str,
                    destination: str
                    ) -> None:
    """
    Upload files from a local directory to a remote directory on the SFTP server

    This function recursively uploads all files and subdirectories from the
    local directory to the specified remote directory on the SFTP server. If the
    remote directory does not exist, it is created. During the upload process,
    the function will print out the status of each file and directory created or
    uploaded.

    Args:
        sftp (pysftp.Connection): The SFTP connection object used to interact
            with the server.
        source (str): The local directory path containing the files to be
            uploaded.
        destination (str): The remote directory path on the SFTP server where
            the files will be uploaded.

    Returns:
        None: This function does not return a value.
    """
    # Check if the SFTP connection is valid
    if sftp is None:
        print("Not connected to SFTP server")
        return

    # Create the main directory on the server
    try:
        sftp.makedirs(destination)
        print(f"Directory created successfully: {destination}")
    except OSError:
        print(f"Directory {destination} already exists on the server")
    except Exception as err:
        print(f"Failed to create directory {destination}: {err}")
        return

    # Recursively go through all files and subdirectories in the local directory
    for root, dirs, files in os.walk(source):
        for dir in dirs:
            # Generate the remote subdirectory path
            remote_dir = os.path.join(
                destination, os.path.relpath(os.path.join(root, dir), source)
                )
            try:
                # Create subdirectories on the server
                sftp.makedirs(remote_dir)
                print(f"Directory created successfully: {remote_dir}")
            except OSError:
                print(f"Directory {remote_dir} already exists on the server")
            except Exception as err:
                print(f"Failed to create directory {remote_dir}: {err}")

        # Upload files
        for fname in files:
            local_file = os.path.join(root, fname)

            remote_file = os.path.join(
                destination, os.path.relpath(local_file, source)
                ).replace(os.sep, "/")# Fix path for SFTP

            try:
                # Upload files to the server
                sftp.put(local_file, remote_file)
                print(f"Successfully uploaded: {local_file} to {remote_file}")
            except SSHException as e:
                print(f"SSH error while uploading {local_file}: {e}")
            except Exception as e:
                print(f"Failed to upload file {local_file}: {e}")


def disconnect_from_sftp(sftp: pysftp.Connection) -> None:
    """
    Disconnects from the SFTP server and closes the connection.

    This function checks if the SFTP connection is active. If it is, it attempts
    to close the connection. If the connection is already closed or was never
    established, it prints a corresponding message.

    Args:
        sftp (pysftp.Connection): The SFTP connection object to be closed.
            If None, the function will print a message indicating that no
            connection was made.

    Returns:
        None
    """
    if sftp is not None:
        try:
            # Close the connection
            sftp.close() 
            print("Successfully disconnected from SFTP server.")
        except Exception as e:
            print(f"Failed to disconnect from SFTP server: {e}")
    else:
        print("No SFTP server was connected.")






