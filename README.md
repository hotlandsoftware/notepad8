# Notepad8
Notepad8 is a text editor designed to be a Notepad++ clone but built to run natively on Linux (it will also run in Windows, and Mac I think... plus whatever can run Python3 and QT6)

## Why?
Recently I switched to Arch Linux from Windows 11, and the experience has been fantastic. However, there was one program that I REALLY missed from Windows, and that was Notepad++. 

Honestly, I have yet to find anything that can replicate not only its ease of use, but its expansive feature set. (I'm aware there is Notepadqq and NotepadNext, but I wasn't happy with eithers current feature set, and I'm not good enough at C++ to contribute to it... and yes, I'm also aware you can run Notepad++ in Wine, but I wanted a native Linux version!)

## Why "Notepad8"?
Notepad2 exists... 2 + 2 = 4... wait, Notepad4 exists! 4 + 4 = 8. So Notepad8! Or something like that

## What's it written in/made with?
Python, QT6, Scintilla.

## What's the goal? How far are you?
The goal is to eventually replicate all of Notepad++'s feature set, but tailored to Linux, plus a few other features I've long wanted.

In terms of how far we are in features, the application is about on par with Notepad++ 1.0 Beta (the original target). It also has a few features found in modern Notepad++ such as restoring unsaved files, custom language lexers, etc.

## Building
Run ```./build.sh``` to build the project!