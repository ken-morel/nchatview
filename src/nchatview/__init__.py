import sys
import os

def choose_app(options: list[str]) -> int:
    print("Which app will you want to use?")
    for idx, option in enumerate(options):
        print(f"{idx + 1}) {option}")
    while True:
        try:
            entry = input("> ")
            if entry == "":
                return 0
            val = int(entry)
            if val < 0 or val > len(options):
                raise ValueError("Invalid option")
            return val
        except ValueError as e:
            print(e)
            continue



def view_file(file: str):
    try:
        if file.startswith("http"):
            match choose_app(["lynx", "xdg-open"]):
                case 1 | 0:
                    os.system("lynx '{file}'")
                case 2:
                    raise Exception()

        ext = file.split(".")[-1]
        if ext == "pdf":
            match choose_app(["zathura", "xdg-open", "okular"]):
                case 1 | 0:
                    os.system(f"zathura '{file}'")
                case 2:
                    raise Exception()
                case 3:
                    os.system(f"okular '{file}'")
        elif ext in ("png", "gif", "apng", "jpg", "jpeg"):
            match choose_app(["magic sixel", "xdg"]):
                case 0 | 1:
                    os.system(f"clear&&convert '{file}' sixel:-")
                    input("hit enter to exit\n> ")
                case 2:
                    raise Exception()
        elif ext in ("md", "txt", "log"):
            os.system(f"nvim '{file}'")
        else:
            raise Exception()
    except Exception:
        os.system(f"xdg-open '{file}'")

def main():
    if len(sys.argv) < 2:
        print("Missing file argument")
        sys.exit(1)
    else:
        file = sys.argv[1]
        view_file(file)


