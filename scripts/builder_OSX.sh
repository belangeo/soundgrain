rm -rf build dist
py2applet --make-setup SoundGrain.py Resources/*
python setup.py py2app
rm -f setup.py
rm -rf build
mv dist SoundGrain_v3.0
cd SoundGrain_v3.0
find . -name .svn -depth -exec rm -rf {} \;
find . -name *.pyc -depth -exec rm -f {} \;
find . -name .* -depth -exec rm -f {} \;
mkdir SoundGrain.app/Contents/Resources/psyco
cp /Library/Frameworks/Python.framework/Versions/2.6/lib/Python2.6/site-packages/psyco/* SoundGrain.app/Contents/Resources/psyco
cd ..
cp -R SoundGrain_v3.0/SoundGrain.app .
tar -cjvf SoundGrain_v3.0.tar.bz2 SoundGrain.app
rm -rf SoundGrain_v3.0
rm -rf SoundGrain.app
