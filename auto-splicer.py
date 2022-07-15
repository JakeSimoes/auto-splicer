import time
import boto3
import json
import tkinter as tk
from pydub import AudioSegment
from pydub.playback import play
import os
from os import listdir
from os.path import isfile, join
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import askdirectory


# TODO: Phoebe splitting for more words
# TODO: A system of picking a better clip over the other when splicing.
choice = 0
while choice != "1" and choice != "2":
    choice = input(
        "Please Input 1 For A New Transcription And 2 For Splicing\n")

# If they choose 1 boto3 setup initializes
if choice == "1":
    job_uri = 0
    saveFiles = [f for f in listdir(os.getcwd()) if
                 isfile(join(os.getcwd(), f))]
    # Credentials are saved to a json file, if it's already a file in the
    # folder it will be used otherwise the program will ask for the info
    # and eventually make a json file if the transcription is successful.
    if "save.json" in saveFiles:
        noCredentials = False
        with open('save.json') as f:
            save = json.load(f)
        key, secretKey, region = save['amazon_info'][0]['access_key'], \
                                 save['amazon_info'][0]['secret_key'], \
                                 save['amazon_info'][0]['region_name']
    else:
        noCredentials = True
        key,secretKey,region = input("Input Your Access Key\n"), \
                               input("Input Your Secret Key\n"), \
                               input("Input Your Region\n")

        data = {}
        data['amazon_info'] = []
        data['amazon_info'].append({
            'access_key': key,
            'secret_key': secretKey,
            'region_name': region
        })



    session = boto3.session.Session(aws_access_key_id=key,
                                      aws_secret_access_key=secretKey,
                                     region_name=region)
    s3 = session.client('s3')
    transcribe = session.client('transcribe')
    job_name = input("Give A Unique Job Name\n")

    # Because the user can always manually upload a file the option is given
    # for them to choose.
    while True:
        localOrNah = input("Input 1 to use a local file or 2 to use a file "
                           "already in a bucket\n")
        if localOrNah == "1":
            while True:
                print("Select a wav file")
                root = tk.Tk()
                root.attributes('-alpha', 0)
                filename = askopenfilename()
                root.destroy()

                # The user is asked to make a new file name and then give the
                # name of the bucket which is then uploaded and the job_uri is
                # set accordingly.
                if ".wav" in str(filename):
                    s3Name = input("Give the file a unique name\n")
                    bucketName = input("Give the bucket name\n")
                    try:
                        print("Uploading file, this may take a while...")
                        s3.upload_file(filename, bucketName, s3Name)
                    except Exception as e:
                        print(e)
                        print("An error occurred while uploading recheck your "
                              "keys, region and bucket")
                        input()
                        exit()
                    job_uri = 's3://{}/{}'.format(bucketName, s3Name)
                    break
                else:
                    print("Unsupported File")
            break
        # If the user wants to use a file already uploaded they are simply asked
        # the bucket and the filename.
        elif localOrNah == "2":
            job_uri = "s3://{}/{}.wav".format(
                 input("Give the bucket name\n"), input("Give the wav file "
                                                       "name\n"))
            break
        else:
            continue
        print("Please enter a valid option")

    # The transcription request is sent to amazon!
    try:
        transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': job_uri},
            MediaFormat='wav',
            LanguageCode='en-US'

        )
    except Exception as e:
        print(e)
        print("An error has occurred while connecting to transcribe recheck "
              "your keys, region and job name")
        input()
        exit()

    # This loops checking the status of the transcription every 5 seconds
    # to report on it.
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED',
                                                                    'FAILED']:
            if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
                print("Transcription Successfully Completed")
                if noCredentials == True:
                    with open('save.json', 'w') as outfile:
                        json.dump(data, outfile)
                input()
                break
            elif status['TranscriptionJob']['TranscriptionJobStatus'] == "FAILED":
                print("Transcription Failure Check the Amazon Console For "
                      "More Info")
                input()
                break
        print("Transcribing...")
        time.sleep(5)

# If the users chooses to splice they are asked for the required files
# using while loops that won't break until they get a file they deem
# acceptable.
elif choice == "2":

    while True:
        print("Select A json File")
        root = tk.Tk()
        root.attributes('-alpha', 0)
        filename = askopenfilename()
        root.destroy()

        if ".json" in str(filename):
            break
        else:
            print("Unsupported File")

    with open(filename) as f:
        data = json.load(f)

    while True:
        # Confidence is transcribes confidence in its guess some
        # may only want better audio clips so the option is here.
        requiredConfidence = float(input("Please give the minimum confidence "
                                         "between 0 and 1\n"))
        if isinstance(requiredConfidence, float):
            if 0.0 <= requiredConfidence <= 1.0:
                break

    while True:
        print("Select a wav file")
        root = tk.Tk()
        root.attributes('-alpha', 0)
        filename = askopenfilename()
        root.destroy()

        if ".wav" in str(filename):
            break
        else:
            print("Unsupported File")
    print("Select a directory for the spliced audio clips")
    root = tk.Tk()
    root.attributes('-alpha', 0)
    audioDir = askdirectory()
    root.destroy()
    print(data['results']['transcripts'][0]['transcript'])
    audio = AudioSegment.from_wav(filename)

    # This is the main splicing loop which uses the timestamps in the json
    # to splice up the given wav file and export it to the chosen folder.
    for i in range(len(data['results']['items'])):
        if "start_time" in data['results']['items'][i]:
            a = float(data['results']['items'][i]['start_time']) * 1000
        if "end_time" in data['results']['items'][i] and float(
                data['results']['items'][i]['alternatives'][0][
                    'confidence']) > requiredConfidence:
            b = float(data['results']['items'][i]['end_time']) * 1000
            split_audio = audio[int(a):int(b)]
            print(data['results']['items'][i]['alternatives'][0]['content'])
            audioDestination = audioDir + '\\' + data['results']['items'][i]['alternatives'][0]['content'].lower() + '.wav'
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

    print("Audio Spliced, type exit or enter a sentence to be constructed...")
    # This loop just checks to see if the inputted sentences words are in the
    # spliced audio folder then splices them together and plays them.
    while True:
        audio = 0
        sentence = input().lower().replace(".", "").replace(",", "").split()
        if sentence[0] == 'exit':
            exit()
        else:
            audioFiles = [f for f in listdir(audioDir) if
                         isfile(join(audioDir, f))]
            for i in sentence:
                if '{}.wav'.format(i) in audioFiles:
                    audio += AudioSegment.from_wav(
                        r"{}/{}.wav".format(audioDir, i))

            if audio != 0:
                play(audio)
