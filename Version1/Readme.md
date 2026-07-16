This current version have very basic Ui

Load the video, trim the and save, at the basic application.


commands i have used.
Step 1: Install PyInstaller
In your terminal, run this command to install the packager:
```
pip install pyinstaller
```

Step 2: Build the Application
Make sure you are in the same directory as your app.py file (D:\KENT STATE UNIVERSITY\job-filler\github\smart_camera\), then run this exact command:
```
pyinstaller --noconfirm --onefile --windowed --collect-all customtkinter app.py
```

What these flags do:

--noconfirm: Automatically overwrites any old build files if you run this command multiple times.

--onefile: Bundles everything (all the Python libraries, OpenCV, and MoviePy) into a single, neat .exe file.

--windowed: Hides the black terminal window so only your sleek, dark-mode UI appears when you open the app.

--collect-all customtkinter: Forces PyInstaller to grab the visual theme files for CustomTkinter, which it sometimes forgets to include.

Step 3: Find Your .exe
Once the terminal finishes processing (it might take a minute or two because it has to compress a lot of data), look in your project folder. PyInstaller will have created a few new folders (build and dist) and a .spec file.

Open the dist (distribution) folder.

Inside, you will find your app.exe.

You can rename this file to VisualTrimmer.exe, move it to your desktop, or send it to anyone else. It now contains everything it needs to run on its own!





---
i got error 
---

1. Create a clean virtual environment
Run this to create an isolated folder called env:
```
python -m venv env
```

2. Activate the clean environment
Run this to step inside that clean room (you will see (env) appear at the start of your terminal line):

```
env\Scripts\activate
```
3. Install strictly what the app needs
Now, install only the core libraries and PyInstaller into this clean space:

```
pip install customtkinter moviepy opencv-python pillow proglog pyinstaller

```


4. Build the app again
Run the exact same command. This time, it will take a fraction of the time because it is ignoring all that machine learning bloat on your PC:

```
pyinstaller --noconfirm --onefile --windowed --collect-all customtkinter app.py
```


i got error : The Fix
Make sure your virtual environment (env) is still activated in your terminal, and run this updated command:

```
pyinstaller --noconfirm --onefile --windowed --collect-all customtkinter --copy-metadata imageio app.py
```

now it is working
