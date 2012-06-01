rm -rf build dist
py2applet --make-setup SoundGrain.py Resources/*
python setup.py py2app --plist=scripts/Info.plist
rm -f setup.py
rm -rf build
mv dist SoundGrain_4.1.1

if cd SoundGrain_4.1.1;
then
    find . -name .svn -depth -exec rm -rf {} \
    find . -name *.pyc -depth -exec rm -f {} \
    find . -name .* -depth -exec rm -f {} \;
else
    echo "Something wrong. SoundGrain_4.1.1 not created"
    exit;
fi

rm SoundGrain.app/Contents/Resources/SoundGrain.ico
rm SoundGrain.app/Contents/Resources/SoundGrainDocIcon.ico

ditto --rsrc --arch i386 SoundGrain.app SoundGrain-i386.app
rm -rf SoundGrain.app
mv SoundGrain-i386.app SoundGrain.app

cd ..
cp -R SoundGrain_4.1.1/SoundGrain.app .

# Fixed wrong path in Info.plist
cd SoundGrain.app/Contents
awk '{gsub("Library/Frameworks/Python.framework/Versions/2.6/Resources/Python.app/Contents/MacOS/Python", "@executable_path/../Frameworks/Python.framework/Versions/2.6/Python")}1' Info.plist > Info.plist_tmp && mv Info.plist_tmp Info.plist

cd ../..
tar -cjvf SoundGrain_4.1.1.tar.bz2 SoundGrain.app
rm -rf SoundGrain_4.1.1
rm -rf SoundGrain.app

svn export . SoundGrain_4.1.1-src
tar -cjvf SoundGrain_4.1.1-src.tar.bz2 SoundGrain_4.1.1-src
rm -R SoundGrain_4.1.1-src
