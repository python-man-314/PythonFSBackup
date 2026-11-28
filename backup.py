try:
    from pathlib import Path
    from datetime import datetime
    import time
    import shutil
    import sys
    import subprocess
    import getpass
    import zipfile

    SKIP_FOLDERS = {Path("/Volumes"), Path("/dev"), Path("/tmp"), Path("/private/tmp"), Path("/cores")}

    def zip_folder(current_folder, zip_file):
        for item in current_folder.iterdir():
            if item.is_symlink() or item.resolve() == Path(selected_drive).resolve() or item in SKIP_FOLDERS:
                continue
            try:
                if item.is_dir():
                    zip_folder(item, zip_file)
                elif item.is_file():
                    zip_file.write(item, arcname=item.relative_to(selected_folder))
            except PermissionError:
                continue

    username = getpass.getuser()

    deps = ["pick", "colorama"]
    print("Checking your operating system")
    print(f"You are on {sys.platform}")
    if sys.platform == "win32":
        deps.append("windows-curses")
    print("Installing dependencies")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", *deps], check=True)
    except subprocess.CalledProcessError as error:
        print(f"Installation of dependencies failed with error code {error.returncode}")
        sys.exit(error.returncode)
        
    from pick import pick
    import colorama
    colorama.init(autoreset=True)
    drives = ["Cancel"]
    if sys.platform == "win32":
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive_path = Path(f"{letter}:/")
            if drive_path.exists():
                drives.append(str(drive_path))
    elif sys.platform == "darwin":
        for drive_path in Path("/Volumes").iterdir():
            drives.append(str(drive_path))
    else:
        for folder in [Path("/media") / username, Path("/mnt"), Path("/run/media") / username]:
            if folder.exists():
                for drive_path in folder.iterdir():
                    drives.append(str(drive_path))
    if len(drives) == 1:
        print(colorama.Fore.RED + "There were no drives found. Check your connection, and try again.")
        sys.exit()
    selected_drive, index = pick(
        drives, "Select a backup drive with the arrow keys."
    )
    print(repr(selected_drive))
    if selected_drive == "Cancel":
        print(colorama.Fore.YELLOW + "Canceled operation")
        exit()
    time.sleep(1)
    print(colorama.Fore.GREEN + f"You have chosen {selected_drive}.")
    time.sleep(2)
    
    home = Path.home()
    folders = [
        "Desktop",
        "Documents",
        "Downloads",
        "Music",
        "Pictures",
        "Videos",
        "User folder",
        "System drive (C: or /)",
        "Back up an external or network (Windows only) drive",
        "Custom",
        "Cancel"
    ]
    folder, index = pick(folders, "What do you want to back up?")
    if folder == "Cancel":
        print(colorama.Fore.YELLOW + "Canceled operation")
        sys.exit()
    elif folder == "System drive (C: or /)":
        selected_folder = Path(Path.home().anchor)
    elif folder == "User folder":
        selected_folder = Path.home()
    elif folder == "Back up an external or network (Windows only) drive":
        backup_drive = []
        source_drives = []
        for drive in drives:
            if drive != selected_drive:
                source_drives.append(drive)
        if len(source_drives) == 1:
            print(colorama.Fore.RED + "There were no drives found to back up. Check the connection, and try again.")
            sys.exit()
        print(colorama.Fore.GREEN + "Searching for backup drives")
        time.sleep(2)
        source_drive, index = pick(
            source_drives, "Select a drive to back up.")
        if source_drive == "Cancel":
            print(colorama.Fore.YELLOW + "Canceled operation")
            sys.exit()
        selected_folder = Path(source_drive)
    elif folder == "Custom":
        if sys.stdin.closed:
            sys.stdin = open("CON") if sys.platform == "win32" else open("/dev/tty")
        raw_path = (
            input("Please enter the path of the file or folder. (Tip: Drag it here) ")
            .strip()
            .strip("\"'")
            .replace("\\ ", " ")
            .replace("\\(", "(")
            .replace("\\)", ")")
            .replace("\\!", "!")
            .replace("\\@", "@")
            .replace("\\#", "#")
            .replace("\\$", "$")
            .replace("\\%", "%")
            .replace("\\^", "^")
            .replace("\\&", "&")
            .replace("\\*", "*")
        )

        selected_folder = Path(raw_path).expanduser()
        if not selected_folder.exists():
            print(colorama.Fore.RED + "The path you have typed does not exist. Check the path, and try again.")
            sys.exit()
    else:
        selected_folder = Path.home() / folder
        if not selected_folder.exists():
            print(colorama.Fore.RED + "That file or folder does not exist. Check the path and try again.")
            sys.exit()
    print(colorama.Fore.GREEN + f"You have selected {selected_folder}")
    src = selected_folder.resolve()
    dst = Path(selected_drive).resolve()

    if (dst == src or src in dst.parents) and not (src == Path("/") and Path("/Volumes") in dst.parents):
        print(colorama.Fore.RED + "Cannot save a backup inside the same folder or drive being backed up!")
        sys.exit()

    confirmation = [
        colorama.Fore.GREEN + "Start backing up",
        "Cancel"
    ]
    print(colorama.Fore.GREEN + f"Backing up folder {selected_folder}")
    print(colorama.Fore.GREEN + f"To drive {selected_drive}")
    time.sleep(1.5)

    confirm_options = ["Start Backup", "Cancel"]
    confirm, index = pick(confirm_options, "Start backup now?")

    if confirm == "Cancel":
        print(colorama.Fore.YELLOW + "Canceled operation")
        sys.exit()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_name = selected_folder.stem if selected_folder.is_file() else selected_folder.name
    if not folder_name:
        folder_name = "drive"

    zip_file_path = Path(selected_drive) / f"{folder_name}_backup_{timestamp}.zip"
    print(colorama.Fore.GREEN + f"Making backup of {selected_folder}. This may take a few moments.")

    try:
        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            if selected_folder.is_file():
                zf.write(selected_folder, arcname=selected_folder.name)
            else:
                zip_folder(selected_folder, zf)
        print(colorama.Fore.GREEN + f"Backed up to {selected_drive}.")
        sys.exit()
    except OSError as e:
        if e.errno in (30, 19):
            print(colorama.Fore.RED + f"The filesystem {selected_drive} is read-only. Try these:\n"
                                      "- Remount the system with write access\n"
                                      "- Format the drive to a filesystem the system can read\n"
                                      "If you can't do any of the above, choose a different drive to back up and try again.")
        elif e.errno == 28:
            print(colorama.Fore.RED + f"The drive {selected_drive} is full. Try these:\n"
                                      "- Free up space on the selected drive.\n"
                                    "If you can't do any of the above, choose a different drive to back up and try again.")
        elif e.errno == 13:
            print(colorama.Fore.RED + f"Python does not have permission to write to or access drive {selected_drive} or folder {selected_folder}. Try these:\n"
                                      "- Run as administrator (Windows) or with sudo access (Linux/Mac).\n"
                                      f"- Give Python permission to write to or access {selected_drive} or {selected_folder}.\n"
                                      f"- Check and modify the permissions of the folder or drive.\n"
                                      f"If you can't do any of the above, choose a different drive or folder to back up and try again.")
        else:
            raise
finally:
    if sys.stdin.closed:
        sys.stdin = open("CON") if sys.platform == "win32" else open("/dev/tty")
        
    input("Press Enter to quit the program ")