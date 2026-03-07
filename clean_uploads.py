import os

folder = "uploads"

for file in os.listdir(folder):
    if file.endswith(".pdf"):
        print("Removing:", file)
        os.remove(os.path.join(folder,file))