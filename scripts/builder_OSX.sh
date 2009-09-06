rm -rf build dist
py2applet --make-setup SoundGrain.py Resources/*
python2.5 setup.py py2app
rm -f setup.py
rm -rf build
#cp scripts/README.txt dist/
mv dist SoundGrain_v1.0
cd SoundGrain_v1.0
find . -name .svn -depth -exec rm -rf {} \;
find . -name *.pyc -depth -exec rm -f {} \;
find . -name .* -depth -exec rm -f {} \;
cd ..
tar -cjvf SoundGrain_v1.0.tar.bz2 SoundGrain_v1.0
#mv SoundGrain/SoundGrain.app SoundGrain.app
rm -rf SoundGrain_v1.0
