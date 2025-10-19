#!/bin/bash
set -e
echo "Building Notepad8..."
rm -rf dist build AppDir *.AppImage

pyinstaller --name "np8" \
    --hidden-import=PyQt6.Qsci \
    --hidden-import=PyQt6.QtPrintSupport \
    --hidden-import=PyQt6.QtNetwork \
    --collect-all PyQt6.Qsci \
    --add-data "src/notepadpypp/icons:icons" \
    --add-data "src/notepadpypp/lexer:lexer" \
    src/notepadpypp/main.py

mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps

cp -r dist/np8/* AppDir/usr/bin/

cat > AppDir/notepadpypp.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Notepad8
Comment=The ass-backwards Notepad++ clone for *nix
Exec=np8
Icon=notepadpypp
Categories=Utility;TextEditor;Development;
Terminal=false
EOF

cp AppDir/notepadpypp.desktop AppDir/usr/share/applications/

if [ ! -f src/notepadpypp/icons/text.png ]; then
    echo "No icon found!"
else
    cp src/notepadpypp/icons/text.png AppDir/notepadpypp.png
    cp src/notepadpypp/icons/text.png AppDir/usr/share/icons/hicolor/256x256/apps/notepadpypp.png
fi

cat > AppDir/AppRun << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export QT_PLUGIN_PATH="${HERE}/usr/bin/PyQt6/Qt6/plugins"

cd "${HERE}/usr/bin"
exec "${HERE}/usr/bin/np8" "$@"
EOF

chmod +x AppDir/AppRun

if [ ! -f appimagetool-x86_64.AppImage ]; then
    echo "Downloading appimagetool..."
    wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x appimagetool-x86_64.AppImage
fi

ARCH=x86_64 ./appimagetool-x86_64.AppImage AppDir np8.AppImage

echo "Done."