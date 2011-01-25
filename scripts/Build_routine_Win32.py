import os

build = True

os.system("python ..\pyinstaller\Configure.py")
os.system('python ..\pyinstaller\Makespec.py -F -c --icon=Resources\SoundGrain.ico "SoundGrain.py"')
if build:
    os.system('python ..\pyinstaller\Build.py "SoundGrain.spec"')
    os.system("svn export . SoundGrain_Win")
    os.system("copy dist\SoundGrain.exe SoundGrain_Win /Y")
    #os.system("copy scripts\README.txt SoiundGrain_Win /Y")
    os.system("rmdir /Q /S SoundGrain_Win\scripts")
    os.remove("SoundGrain_Win/SoundGrain.py")
    os.remove("SoundGrain_Win/Resources/SoundGrain.icns")
    os.remove("SoundGrain_Win/Resources/SoundGrainDocIcon.icns")
    os.remove("SoundGrain.spec")
    os.system("rmdir /Q /S build")
    os.system("rmdir /Q /S dist")

