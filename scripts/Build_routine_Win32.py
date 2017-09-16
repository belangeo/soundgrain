import os

flags = "--clean -F -c"
hidden = "--hidden-import wx.adv --hidden-import wx.html --hidden-import wx.xml"
icon = "--icon=Resources\SoundGrain.ico"
os.system('pyinstaller %s %s %s "SoundGrain.py"' % (flags, hidden, icon))

os.system("git checkout-index -a -f --prefix=SoundGrain_Win/")
os.system("copy dist\SoundGrain.exe SoundGrain_Win /Y")
os.system("rmdir /Q /S SoundGrain_Win\scripts")
os.remove("SoundGrain_Win/SoundGrain.py")
os.remove("SoundGrain_Win/.gitignore")
os.remove("SoundGrain_Win/setup.py")
os.remove("SoundGrain_Win/Resources/SoundGrain.icns")
os.remove("SoundGrain_Win/Resources/SoundGrainDocIcon.icns")
os.remove("SoundGrain.spec")
os.system("rmdir /Q /S build")
os.system("rmdir /Q /S dist")
for f in os.listdir(os.getcwd()):
    if f.startswith("warn") or f.startswith("logdict"):
        os.remove(f)

