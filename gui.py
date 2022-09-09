import os.path
import sys
import random
import json
import time
import requests
import boto3
from os import listdir, getcwd, mkdir
from os.path import isfile, join
from pydub import AudioSegment
from pydub.playback import play
from PyQt5.QtWidgets import QMainWindow, QApplication, QGridLayout, QWidget, QTextEdit, QPushButton, QFileDialog, QLineEdit, QMessageBox, QLabel
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot, Qt
import threading

# Simple Audio is also a dependency, without it this will crash!

class KeyWindow(QWidget):
    def __init__(self, mainWindow):
        super().__init__()
        layout = QGridLayout()
        self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, False)
        self.setWindowTitle("AWS Info")
        self.setStyleSheet(open('style.css').read())

        # Grabbing saved data to display in the fields
        if "save.json" in mainWindow.saveFiles:
            with open('save.json') as f:
                save = json.load(f)
            x, y, z, b = save['amazon_info'][0]['access_key'], \
                         save['amazon_info'][0]['secret_key'], \
                         save['amazon_info'][0]['region_name'], \
                         save['amazon_info'][0]['bucket_name']
        else:
            # Blank data if nothing is found
            x, y, z, b = "", "", "", ""

        # Creating the AWS key label and field.
        self.keyLabel = QLabel("AWS Key:")
        layout.addWidget(self.keyLabel, 0, 0)
        self.keyField = QLineEdit(x)
        layout.addWidget(self.keyField, 0, 1)
        # Creating the AWS secret key label and field.
        self.scKeyLabel = QLabel("Secret Key:")
        layout.addWidget(self.scKeyLabel, 1, 0)
        self.scKeyField = QLineEdit(y)
        layout.addWidget(self.scKeyField, 1, 1)
        # Creating the region label and field.
        self.regionLabel = QLabel("Region:")
        layout.addWidget(self.regionLabel, 2, 0)
        self.regionField = QLineEdit(z)
        layout.addWidget(self.regionField, 2, 1)
        # Bucket label and field
        self.bucketLabel = QLabel("Bucket:")
        layout.addWidget(self.bucketLabel, 3, 0)
        self.bucketField = QLineEdit(b)
        layout.addWidget(self.bucketField, 3, 1)
        # Making a cancel button
        self.cancelButton = QPushButton("Cancel")
        layout.addWidget(self.cancelButton, 4, 0)
        self.cancelButton.clicked.connect(self.close)
        # Making an apply/set button
        self.setButton = QPushButton("Set")
        layout.addWidget(self.setButton, 4, 1)

        # Once the user is done and clicks "Set" write the values to the json
        self.setButton.clicked.connect(self.writeValues)
        self.setLayout(layout)

    def writeValues(self):
        # Structure the data into a dictionary in a list
        data = {}
        data['amazon_info'] = [{
            'access_key': self.keyField.text(),
            'secret_key': self.scKeyField.text(),
            'region_name': self.regionField.text(),
            'bucket_name': self.bucketField.text()
        }]
        # Write or amend the file
        with open('save.json', 'w') as outfile:
            json.dump(data, outfile)
        self.close()


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.session, self.s3, self.key, self.secretKey, self.region, self.bucket = [None for _ in range(6)]
        # Getting the folder contents to check for saved data
        self.saveFiles = [f for f in listdir(getcwd()) if
                     isfile(join(getcwd(), f))]
        self.setStyleSheet(open('style.css').read())
        self.setWindowTitle("Auto Splicer Ver. 0.01")
        app.setStyle("Fusion")
        layout = QGridLayout()

        # Adding widgets to the window.
        self.fileButton = QPushButton("File")
        self.fileButton.clicked.connect(self.fileSelection)
        layout.addWidget(self.fileButton, 0, 0, alignment=Qt.AlignTop)

        self.keysButton = QPushButton("Keys")
        self.keysButton.clicked.connect(self.keysWindow)
        layout.addWidget(self.keysButton, 1, 0)

        self.wordBankList = QTextEdit()
        self.wordBankList.setReadOnly(True)
        layout.addWidget(self.wordBankList, 0, 1, 1, 2)

        self.wordInput = QLineEdit("Hello World")
        self.wordInput.setDisabled(True)
        self.wordInput.textChanged[str].connect(self.wordSuggestions)
        layout.addWidget(self.wordInput, 1, 1)

        self.playButton = QPushButton("Play")
        layout.addWidget(self.playButton, 1, 2)
        self.playButton.clicked.connect(self.audioMixer)
        self.playButton.setDisabled(True)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        self.show()

        # Open the key entry window if no saved data is found
        if "save.json" not in self.saveFiles:
            self.keysWindow()



    def keysWindow(self):
        # Creates an object for the window and shows it
        self.w = KeyWindow(self)
        self.w.show()

    def fileSelection(self):
        filename = QFileDialog.getOpenFileName()

        if ".json" in filename[0]:
            print("Json detected pre-sliced files!")
        elif ".wav" in filename[0]:
            self.wavUpload(filename[0])
        elif not filename[0]:
            pass
        else:
            self.sendMessage("Only .WAV files are supported!")

    def sendMessage(self, msg_text, error=True):
        msg = QMessageBox()
        msg.setStyleSheet(open('style.css').read())
        if error:
            msg.setWindowTitle("Error")
            msg.setIcon(QMessageBox.Critical)
        else:
            msg.setWindowTitle("Info")
        msg.setText(msg_text)
        msg.exec_()

    def wavUpload(self, file):
        self.grabCredentials()
        self.startSession()
        transcribe = self.session.client('transcribe')
        job_name = str(random.randint(0, 10000))

        s3Name = str(random.randint(0, 10000))

        try:
            print("Uploading file, this may take a while...")
            self.s3.upload_file(file, self.bucket, s3Name)
            job_uri = 's3://{}/{}'.format(self.bucket, s3Name)
        except Exception as e:
            print(e)
            self.sendMessage("Recheck Credentials")
            return

        # Starting a transcribe job with the uploaded file
        print("Transcribing")
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': job_uri},
            MediaFormat='wav',
            LanguageCode='en-US'

        )

        # Checking if the transcription executed properly
        print("Transcribing loop")
        while True:
            status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED',
                                                                        'FAILED']:
                if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
                    self.sendMessage("Transcription Success", False)
                    break
                elif status['TranscriptionJob']['TranscriptionJobStatus'] == "FAILED":
                    self.sendMessage("Transcription Failure")
                    return
            time.sleep(5)
        try:
            url = requests.get(status['TranscriptionJob']['Transcript']['TranscriptFileUri'])
            transcription = json.loads(url.text)
        except Exception as e:
            self.sendMessage("Transcript Retrieval Error")
            return

        self.spliceAudio(file, transcription, job_name)

    def spliceAudio(self, audio_file, json_file, job_name, required_confidence=0.1):
        # This is the main splicing loop which uses the timestamps in the json
        # to splice up the given wav file and export it to the chosen folder.
        print("Hello!")
        audio = AudioSegment.from_wav(audio_file)
        if not os.path.exists(getcwd() + '\\audio\\'):
            try:
                mkdir(getcwd() + '\\audio\\')
            except Exception as e:
                self.sendMessage(e, True)

        self.audioDirectory = getcwd() + '\\audio\\{}\\'.format(str(job_name))
        mkdir(self.audioDirectory)
        self.wordList = []
        print("Hello before the try!")
        try:
            print("Hello from the try!")
            for i in range(len(json_file['results']['items'])):
                if "start_time" in json_file['results']['items'][i]:
                    a = float(json_file['results']['items'][i]['start_time']) * 1000
                if "end_time" in json_file['results']['items'][i] and float(
                        json_file['results']['items'][i]['alternatives'][0][
                            'confidence']) > required_confidence:
                    b = float(json_file['results']['items'][i]['end_time']) * 1000
                    split_audio = audio[int(a):int(b)]
                    self.wordList.append(json_file['results']['items'][i]['alternatives'][0][
                        'content'].lower())
                    audioDestination = self.audioDirectory + json_file['results']['items'][i]['alternatives'][0][
                        'content'].lower() + '.wav'

                    # An unknown error occurred which was likely an error with PyDub
                    # so a try statement is used so that the program carries on.
                    # This try statement checks if there is already an audio clip with
                    # the same name and picks the longest one between the two.
                    try:
                        if isfile(audioDestination):
                            if AudioSegment.from_wav(audioDestination).frame_count() > split_audio.frame_count():
                                pass
                            else:
                                split_audio.export(audioDestination, format="wav")
                        else:
                            split_audio.export(audioDestination, format="wav")

                    except Exception as e:
                        print("Encountered an error, skipping a word...")
        except Exception as e:
            self.sendMessage("Malformed Data")
        self.sendMessage("Done!", error=False)
        self.playButton.setDisabled(False)
        self.wordInput.setDisabled(False)

    def audioMixer(self):
        audio = 0
        sentence = self.wordInput.text().lower().replace(".", "").replace(",", "").split()

        audioFiles = [f for f in listdir(self.audioDirectory) if
                      isfile(join(self.audioDirectory, f))]

        for i in sentence:
            if '{}.wav'.format(i) in audioFiles:
                audio += AudioSegment.from_wav(
                    r"{}/{}.wav".format(self.audioDirectory, i))

        if audio != 0:
            t = threading.Thread(target=play, args=(audio,))
            t.start()

    def startSession(self):
        if self.session == None:
            self.session = boto3.session.Session(aws_access_key_id=self.key,
                                        aws_secret_access_key=self.secretKey,
                                        region_name=self.region)
            self.s3 = self.session.client('s3')

    def grabCredentials(self):
        with open('save.json') as f:
            save = json.load(f)
        self.key, self.secretKey, self.region, self.bucket = save['amazon_info'][0]['access_key'], \
                                                             save['amazon_info'][0]['secret_key'], \
                                                             save['amazon_info'][0]['region_name'], \
                                                             save['amazon_info'][0]['bucket_name']

    def wordSuggestions(self):
        try:
            if self.wordInput.text():
                word = self.wordInput.text().lower().replace(".", "").replace(",", "").split(" ")[-1]
                self.wordBankList.setText(" ".join([i for i in self.wordList if word in i]))
            else:
                self.wordBankList.setText(" ".join(self.wordList))
        except Exception as e:
            print(e)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec())
