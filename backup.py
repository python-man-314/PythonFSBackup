try:
    from pathlib import Path
    from datetime import datetime
    import time
    import shutil
    import sys
    import subprocess
    import getpass
    
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
        if Path(selected_drive).resolve() == selected_folder.resolve() or selected_folder.resolve() in Path(selected_drive).resolve().parents:
            print(colorama.Fore.RED + "Cannot save a backup inside the same folder or drive being backed up!")
            sys.exit()
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
        raw_path = input("Please enter the path of the file or folder. (Tip: Drag it here) ").strip().strip("'").strip('"')
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
    folder_name = selected_folder.name
    if not folder_name:
        folder_name = "drive"
    zip_base_path = Path(selected_drive) / f"{folder_name}_backup_{timestamp}"
    print(colorama.Fore.GREEN + f"Making backup of {selected_folder}. This may take a few moments.")
    if selected_folder.is_dir():
        final_zip = shutil.make_archive(str(zip_base_path), "zip", str(selected_folder))
    else:
        final_zip = shutil.make_archive(
            str(zip_base_path),
            "zip",
            str(selected_folder.parent),
            selected_folder.name
        )
    print(colorama.Fore.GREEN + f"Backed up to {selected_drive}.")
    sys.exit()
finally:
    if sys.stdin.closed:
        sys.stdin = open("CON") if sys.platform == "win32" else open("/dev/tty")
        
    input("Press Enter to quit the program ")