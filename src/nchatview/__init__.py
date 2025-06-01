import sys
import os
import time


class XdgOpen(Exception):
    pass


class ExtenalXdgOpen(XdgOpen):
    pass


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
        time.sleep(1)
        if file.startswith("http"):
            os.system("lynx '{file}'")
        ext = file.split(".")[-1]
        if ext in ("png", "gif", "apng", "jpg", "jpeg", "webp"):
            os.system(f"clear&&convert '{file}' gif:- | chafa")
            input("\n\nhit enter to exit\n> ")
        elif ext == "pdf":
            from . import pdfview

            pdfview.view_file(file)
        elif ext == "txt":
            from . import mdview

            os.system("clear")

            mdview.view_file(file)
            input("Press enter to exit\n> ")
        elif ext in ("md", "txt", "log"):
            os.system(f"nvim '{file}'")
        elif ext in ("mp3", "oga"):
            from . import audioplayer

            audioplayer.play_file(file)
        else:
            os.system(f"xdg-open '{file}'")
    except KeyboardInterrupt:
        os.system(f"swaymsg exec xdg-open '{file}'")
    except XdgOpen:
        os.system(f"xdg-open '{file}'")


def main():
    if len(sys.argv) < 2:
        print("Missing file argument")
        sys.exit(1)
    else:
        file = sys.argv[1]
        view_file(file)
