rm -rf build dist

export DMG_DIR="SoundGrain 6.0.1"
export DMG_NAME="SoundGrain_6.0.1.dmg"

python3.6 setup.py py2app --plist=scripts/Info.plist

rm -rf build
mv dist SoundGrain_OSX

if cd SoundGrain_OSX;
then
    find . -name .git -depth -exec rm -rf {} \
    find . -name *.pyc -depth -exec rm -f {} \
    find . -name .* -depth -exec rm -f {} \;
else
    echo "Something wrong. SoundGrain_OSX not created"
    exit;
fi

rm SoundGrain.app/Contents/Resources/SoundGrain.ico
rm SoundGrain.app/Contents/Resources/SoundGrainDocIcon.ico

# keep only 64-bit arch
ditto --rsrc --arch x86_64 SoundGrain.app SoundGrain-x86_64.app
rm -rf SoundGrain.app
mv SoundGrain-x86_64.app SoundGrain.app

# Fixed wrong path in Info.plist
cd SoundGrain.app/Contents
awk '{gsub("@executable_path/../Frameworks/Python.framework/Versions/2.7/Python", "@executable_path/../Frameworks/Python.framework/Versions/3.6/Python")}1' Info.plist > Info.plist_tmp && mv Info.plist_tmp Info.plist
awk '{gsub("Library/Frameworks/Python.framework/Versions/3.6/bin/python3.6", "@executable_path/../Frameworks/Python.framework/Versions/3.6/Python")}1' Info.plist > Info.plist_tmp && mv Info.plist_tmp Info.plist

cd ../../..
cp -R SoundGrain_OSX/SoundGrain.app .

echo "assembling DMG..."
mkdir "$DMG_DIR"
cd "$DMG_DIR"
cp -R ../SoundGrain.app .
ln -s /Applications .

cd ..

hdiutil create "$DMG_NAME" -srcfolder "$DMG_DIR"

rm -rf "$DMG_DIR"
rm -rf SoundGrain_OSX
rm -rf SoundGrain.app
