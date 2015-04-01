import os, shutil, sys

version = sys.version_info[:2]

os.system('C:\Python%d%d\Scripts\pyi-makespec -F -c --icon=Resources\SoundGrain.ico "SoundGrain.py"' % version)
os.system('C:\Python%d%d\Scripts\pyi-build "SoundGrain.spec"' % version)

os.system("python ..\pyinstaller\Configure.py")
os.system('python ..\pyinstaller\Makespec.py -F -c --icon=Resources\SoundGrain.ico "SoundGrain.py"')

os.system("svn export . SoundGrain_Win")
os.system("copy dist\SoundGrain.exe SoundGrain_Win /Y")
os.system("rmdir /Q /S SoundGrain_Win\scripts")
os.remove("SoundGrain_Win/SoundGrain.py")
os.remove("SoundGrain_Win/Resources/SoundGrain.icns")
os.remove("SoundGrain_Win/Resources/SoundGrainDocIcon.icns")
os.remove("SoundGrain.spec")
os.system("rmdir /Q /S build")
os.system("rmdir /Q /S dist")
for f in os.listdir(os.getcwd()):
    if f.startswith("warn") or f.startswith("logdict"):
        os.remove(f)

