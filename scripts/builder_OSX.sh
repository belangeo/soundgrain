rm -rf build dist
py2applet --make-setup SoundGrain.py Resources/*
python2.5 setup.py py2app
rm -f setup.py
rm -rf build
cp scripts/README.txt dist/
mv dist SoundGrain_v2.0
cd SoundGrain_v2.0
find . -name .svn -depth -exec rm -rf {} \;
find . -name *.pyc -depth -exec rm -f {} \;
find . -name .* -depth -exec rm -f {} \;
mkdir SoundGrain.app/Contents/Resources/psyco
cp /Library/Frameworks/Python.framework/Versions/2.5/lib/Python2.5/site-packages/psyco/* SoundGrain.app/Contents/Resources/psyco
cd ..
tar -cjvf SoundGrain_v2.0.tar.bz2 SoundGrain_v2.0
rm -rf SoundGrain_v2.0
