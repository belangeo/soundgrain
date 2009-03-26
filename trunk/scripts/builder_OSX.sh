rm -rf build dist
py2applet --make-setup SoundGrain.py Resources/*
python setup.py py2app
rm -f setup.py
rm -rf build
#cp scripts/README.txt dist/
mv dist SoundGrain
cd SoundGrain
find . -name .svn -depth -exec rm -rf {} \;
find . -name *.pyc -depth -exec rm -f {} \;
find . -name .* -depth -exec rm -f {} \;
cd ..
tar -cjvf SoundGrain.tar.bz2 SoundGrain
#mv SoundGrain/SoundGrain.app SoundGrain.app
rm -rf SoundGrain
