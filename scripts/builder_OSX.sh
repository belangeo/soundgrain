rm -rf build dist

export DMG_DIR="SoundGrain 6.0.0"
export DMG_NAME="SoundGrain_6.0.0.dmg"
export SRC_DIR="SoundGrain_6.0.0-src"
export SRC_TAR="SoundGrain_6.0.0-src.tar.bz2"

py2applet --make-setup --argv-emulation=0 SoundGrain.py Resources/*
python setup.py py2app --plist=scripts/Info.plist
rm -f setup.py
rm -rf build
mv dist SoundGrain_OSX

if cd SoundGrain_OSX;
then
    find . -name .svn -depth -exec rm -rf {} \
    find . -name *.pyc -depth -exec rm -f {} \
    find . -name .* -depth -exec rm -f {} \;
else
    echo "Something wrong. SoundGrain_OSX not created"
    exit;
fi

rm SoundGrain.app/Contents/Resources/SoundGrain.ico
rm SoundGrain.app/Contents/Resources/SoundGrainDocIcon.ico

ditto --rsrc --arch x86_64 SoundGrain.app SoundGrain-x86_64.app
rm -rf SoundGrain.app
mv SoundGrain-x86_64.app SoundGrain.app

cd ..
cp -R SoundGrain_OSX/SoundGrain.app .

echo "assembling DMG..."
mkdir "$DMG_DIR"
cd "$DMG_DIR"
cp -R ../SoundGrain.app .
ln -s /Applications .

cd ..

hdiutil create "$DMG_NAME" -srcfolder "$DMG_DIR"

svn export . "$SRC_DIR"
tar -cjvf "$SRC_TAR" "$SRC_DIR"
rm -R "$SRC_DIR"

rm -rf "$DMG_DIR"
rm -rf SoundGrain_OSX
rm -rf SoundGrain.app
