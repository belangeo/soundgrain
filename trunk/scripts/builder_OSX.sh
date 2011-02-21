rm -rf build dist
py2applet --make-setup SoundGrain.py Resources/*
python setup.py py2app --plist=scripts/Info.plist
rm -f setup.py
rm -rf build
mv dist SoundGrain_v4.0.1
cd SoundGrain_v4.0.1
find . -name .svn -depth -exec rm -rf {} \;
find . -name *.pyc -depth -exec rm -f {} \;
find . -name .* -depth -exec rm -f {} \;
cd ..
cp -R SoundGrain_v4.0.1/SoundGrain.app .
#tar -cjvf SoundGrain_v4.0.tar.bz2 SoundGrain.app
rm -rf SoundGrain_v4.0.1
#rm -rf SoundGrain.app
