import os
from werkzeug.utils import secure_filename
from app import standardize_filename, app

folder = app.config['UPLOAD_FOLDER']
print(f"Renaming files in {folder}...")
count = 0
for f in os.listdir(folder):
    if os.path.isfile(os.path.join(folder, f)):
        new_name = secure_filename(standardize_filename(f))
        if new_name != f:
            os.rename(os.path.join(folder, f), os.path.join(folder, new_name))
            print(f"Renamed: {f} -> {new_name}")
            count += 1
print(f"Total renamed: {count}")
