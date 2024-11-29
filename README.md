# NotepadPy++
NotepadPy++ is a text editor - more specifically, a Notepad++ clone, but built to run on Linux (it will also run in Windows, and Mac I think, plus whatever can run Python3 and QT6)

## Why?
Recently I switched to Arch Linux from Windows 11, and the experience has been fantastic. However, there was one program that I REALLY missed from Windows, and that was Notepad++. 

Honestly, I have yet to find anything that can replicate not only its ease of use, but its expansive feature set. (I'm aware there is Notepadqq and NotepadNext, but I wasn't happy with its current feature set, and I'm not good enough at C++ to contribute to it... and I'm also aware you can run Notepad++ in Wine, but I wanted a native Linux version!)

## What's it written in/made with?
Python 3, QT6, and Scintilla.

## What's the goal/endgame?
To eventually replicate Notepad++'s entire feature set. For the initial release, I targeted the very first version of Notepad++ (1.0.0) as a base. I will expand from there. So far, I've got syntax highlighting, UI customization, session restore, and some of the search features implemented. Very basic but its working.

## Will it ever be finished?
Progress is going well, so I think I have a good shot. I appreciate any help!

## Building
Run ```pyinstaller main.spec``` to build the project!