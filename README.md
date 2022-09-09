# An Amazon Transcribe powered audio splicer.

This is a Python program which utilizes several libraries and Amazon Transcribe to splice words in audio.
auto-splicer.py Provides a command-line prompt while gui.py provides an interface.
To use the program make sure you have tkinter, PyDub, PyQt5, SimpleAudio and boto3 installed.
The program will also require Amazon console credentials and an S3 bucket; All of which can be inserted in the keys window.
Both of these amazon services are free as long as you don't run past the free quota (which is quite large).

Once all that has been met press the file button and upload a .WAV file. 
Your file will be uploaded to the bucket and transcribed. 
The results are then retrieved, used to splice the audio clip, and voila.
Type in whatever sentence you want with the help of the word bank and click play!

![ezgif-5-9fffb5a0fd](https://user-images.githubusercontent.com/60676244/189252161-af69d017-752b-4968-b093-4ec7b1506faf.gif)
