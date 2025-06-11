import os

EXCLUDED_DIRS = {
    '.git',
    'flask_session',
    '.gitattributes',
    '.gitignore',
    'Arborescence.py',
    'Arborescence.txt',
    'translator_env',
    'node_modules',
    'package-lock.json',
    'package.json',
    '__pycache__',
    'A_SUPPRIMER',
    'Arborescence.py',
    'arborescence.txt',
    'test',
    'bluestacks_automation.code-workspace',
    '.vscode',
    'auto_screenshot_env',
}

COLLAPSED_DIRS = {
    'venv',
}

def is_excluded(path):
    """
    Vérifie si un chemin contient un des dossiers ou fichiers exclus.
    """
    for excluded in EXCLUDED_DIRS:
        if excluded in path.split(os.sep):
            return True
    return False

def draw_tree(directory, prefix="", output_file=None):
    entries = sorted(os.listdir(directory))
    entries = [
        e for e in entries
        if not is_excluded(os.path.relpath(os.path.join(directory, e), start=base_directory))
    ]

    for i, entry in enumerate(entries):
        path = os.path.join(directory, entry)
        connector = "├── " if i < len(entries) - 1 else "└── "
        line = f"{prefix}{connector}{entry}\n"
        print(line, end="")
        if output_file:
            output_file.write(line)

        if os.path.isdir(path):
            rel_path = os.path.relpath(path, start=base_directory)
            dir_name = os.path.basename(path)

            if dir_name in COLLAPSED_DIRS:
                continue  # Ne pas descendre dedans

            if dir_name == "flags":
                files_in_flags = sorted(os.listdir(path))
                for j, flag_file in enumerate(files_in_flags[:3]):
                    sub_connector = "├── " if j < len(files_in_flags[:3]) - 1 else "└── "
                    flag_line = f"{prefix}{connector}{sub_connector}{flag_file}\n"
                    print(flag_line, end="")
                    if output_file:
                        output_file.write(flag_line)
                if len(files_in_flags) > 3:
                    more_line = f"{prefix}{connector}    ...\n"
                    print(more_line, end="")
                    if output_file:
                        output_file.write(more_line)
            else:
                new_prefix = prefix + ("│   " if i < len(entries) - 1 else "    ")
                draw_tree(path, new_prefix, output_file)


def main():
    global base_directory
    base_directory = os.getcwd()

    output_file_path = os.path.join(base_directory, "arborescence.txt")
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        output_file.write(f"Arborescence du répertoire : {base_directory}\n\n")
        print(f"Arborescence du répertoire : {base_directory}\n")
        draw_tree(base_directory, output_file=output_file)

    print(f"\nL'arborescence a été sauvegardée dans le fichier : {output_file_path}")

if __name__ == "__main__":
    main()
