import tempfile
import hashlib
import os
import time
import random
from typing import Optional
from threading import Thread


class PdfViewer:
    pdf_path: str
    temp_folder: str
    info: dict
    page_index: int
    should_run: bool
    generating: Optional[int]

    def __init__(self, pdf_path):
        self.generating = None
        self.page_index = 0
        self.pdf_path = pdf_path
        self.info = {}
        self.get_temp_folder()
        self.get_info()

    def generate_pages_in_background(self):
        Thread(
            target=self._generate_worker,
        ).start()

    def _generate_worker(self):
        print("Generating pages in background...")
        for i in range(self.npages):
            if not self.should_run:
                break
            self.generating = i
            print("Worker Generating page", i + 1, "of", self.npages, end="...\r")
            self.get_page_view(i)
            self.generating = None
        print("Worker completed generating all pages.")

    def get_info(self):
        print("Getting PDF info...")
        os.system(f"pdfinfo '{self.pdf_path}' >> {self.temp_folder}/pdfinfo.txt")
        with open(self.temp_folder + "/pdfinfo.txt", "r") as file:
            for line in file:
                (key, value) = map(str.strip, line.split(":", 1))
                self.info[key.lower()] = value
        self.npages = int(self.info.get("pages", 1))

    def get_temp_folder(self):
        path = tempfile.gettempdir()
        hash = hashlib.md5(self.pdf_path.encode()).hexdigest()
        self.temp_folder = path + f"/pdfview/{hash}"
        os.makedirs(self.temp_folder, exist_ok=True)

    def run(self):
        os.system("clear")
        self.should_run = True
        self.generate_pages_in_background()
        while self.should_run:
            self.show_page()
            print(
                "q to quit, n for next, p for previous, R to clear file cache and reaload"
            )
            self.handle_input()
            os.system("clear")

    def show_page(self):
        if self.page_index == self.generating:
            print(
                f"Page {self.page_index + 1} is being generated, please wait...",
                end="\r",
            )
        while self.page_index == self.generating:
            time.sleep(0.1)
        tmpimgage = self.get_page_view(self.page_index)
        os.system(f"chafa '{tmpimgage}'")
        print(f"\nPage {self.page_index + 1} of {self.npages}")

    def get_page_view(self, page_index: int) -> str:

        path = self.temp_folder + f"/page{page_index}.png"
        if os.path.exists(path):
            return path
        else:
            print(f"Generating page {page_index + 1} view...", end="\r")
            os.system(
                f"convert '{self.pdf_path}[{page_index}]'"
                + f" -density 150 -quality 100 {path}"
            )
            return path

    def handle_input(self):
        key = input()
        if key.isnumeric():
            pageidx = int(key)
            if pageidx > 0 and pageidx <= int(self.info["pages"]):
                self.page_index = pageidx - 1
            else:
                print(f"Invalid page index {pageidx}", end="\r")
        if key == "q":
            self.should_run = False
        elif key == "R":
            os.system(f"rm -rf '{self.temp_folder}'")
            self.get_temp_folder()
            self.get_info()
        elif key == "n":
            if self.page_index < int(self.info["pages"]) - 1:
                self.page_index += 1
            else:
                print("No next page", end="\r")
        elif key == "p":
            if self.page_index > 0:
                self.page_index -= 1
            else:
                print("No previous page", end="\r")


def view_file(pdf_path: str):
    print("Viewing PDF file:", pdf_path)
    print(os.path.exists(pdf_path))
    PdfViewer(pdf_path).run()
