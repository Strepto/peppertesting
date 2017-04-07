#!/usr/bin/env python

import sys
sys.path.append("/home/nao/.local/share/PackageManager/apps/")
import qi
#import numpy as NP
import cognitive_face as CF
import time



class SopraSteriaGreeter(object):
    
    
    photoPath = '/home/nao/recordings/cameras/'
    groupID = 1337
    KEY = '6125152da7554bca93dba66b0da57699'

    def __init__(self, application):
        # Getting a session that will be reused everywhere
        self.application = application
        self.session = application.session
        self.service_name = self.__class__.__name__
        
        # Getting a logger. Logs will be in /var/log/naoqi/servicemanager/{application id}.{service name}
        self.logger = qi.Logger(self.service_name)
        # Do some initializations before the service is registered to NAOqi
        self.logger.info("Initializing...")
        # Insert init functions here
        self.logger.info("Initialized!")
        
        
        # Connect to services
        self.connect_services()
        
    @qi.nobind
    def connect_services(self):
        # connect all services required by your module
        # done in async way over 30s,
        # so it works even if other services are not yet ready when you start your module
        # this is required when the service is autorun as it may start before other modules...
        self.logger.info('Connecting services...')
        self.services_connected = qi.Promise()
        services_connected_fut = self.services_connected.future()

        def get_services():
            try:
                self.logger.info('yo')
                self.memory = self.session.service('ALMemory')
                self.faceRecognition = self.session.service("ALFaceDetection")
                self.photoCapture = self.session.service("ALPhotoCapture")
                self.dialog = self.session.service("ALDialog")
                self.textToSpeech = self.session.service("ALTextToSpeech")
                self.personEnteredZone = self.session.service("ALEngagementZones") 
                self.peoplePerception = self.session.service("ALPeoplePerception")
                self.faceDetection = self.session.service("ALFaceDetection")
                
                # connect other services if needed...
                self.logger.info('All services are now connected')
                self.services_connected.setValue(True)
            except RuntimeError as e:
                self.logger.warning('Still missing some service:\n {}'.format(e))

        get_services_task = qi.PeriodicTask()
        get_services_task.setCallback(get_services)
        get_services_task.setUsPeriod(int(2*1000000))  # check every 2s
        get_services_task.start(True)
        try:
            services_connected_fut.value(30*1000)  # timeout = 30s
            get_services_task.stop()
        except RuntimeError:
            get_services_task.stop()
            self.logger.error('Failed to reach all services after 30 seconds')
            raise RuntimeError


    @qi.nobind
    def start_app(self):
        # do something when the service starts
        print "Starting app..."
        
        # Establishing signal listeners 
        self.peoplePerception.setMaximumDetectionRange(1.5)
        self.textToSpeech.say("YOLO")
        self.peoplePerception.justArrived.connect(self.newPersonDetected)
#        self.faceDetected_signal = self.memory.subscriber("FaceDetected").signal
#        self.faceDetected_signal.connect(self.recognizePerson())
#        self.faceDetection.learnFace('tempFace'+str(time.time())
#        self.memory.insertData("SopraSteriaGreeter/tempFace", 10)
        # @TODO: insert whatever the app should do to start
        self.logger.info("Started!")
        
        
        
        

    @qi.nobind
    def stop_app(self):
        # To be used if internal methods need to stop the service from inside.
        # external NAOqi scripts should use ALServiceManager.stopService if they need to stop it.
        self.logger.info("Stopping service...")
        self.application.stop()
        self.logger.info("Stopped!")

    @qi.nobind
    def cleanup(self):
        # called when your module is stopped
        self.logger.info("Cleaning...")
        # @TODO: insert cleaning functions here
        self.logger.info("Cleaned!")

    def newPersonDetected(self, numPeople):
        
        self.textToSpeech.say('Hi there. Look me in the eyes please, I\'ll see if I can remember you.')
        self.learnFace(numTries=2)
        # if numPeople > 1:
        #     self.textToSpeech.say('Its too crowded here. I can see ' + str(numPeople) + ' people.')

    def learnFace(self, numTries=1):
        if(numTries > 0):
            isFaceLearned = self.faceDetection.learnFace(str(time.time()))
            self.logger.info(isFaceLearned)
            if isFaceLearned:
                self.recognizePerson()
            else:
                self.textToSpeech.say('Hmmmm')
                self.learnFace(numTries-1)

        else:
            self.textToSpeech.say('Hide and come back for another try!')


    def recognizePerson(self):
        photoPath = self.takePhoto()
        self.logger.info(photoPath)
        CF.Key.set(self.KEY)
        
        #faceServiceClient = FaceServiceClient(self.KEY)
        #photoStream = open(photoPath, "r")
        
        face = CF.face.detect(photoPath)
        # self.logger.info(CF.person_group.create(groupID, "Pepper"))
        asmund = CF.person.create(self.groupID, "AAsmund Pedersen Hugo")
        # asmund = CF.person.get(groupID, '8d11e6d0-1163-4adc-a271-b66e315d9277')
        asmundID = asmund.get('personId')
        self.logger.info(CF.person.add_face('https://i.imgur.com/hgErMru.png', self.groupID, asmundID))       
        self.logger.info(CF.person_group.train(self.groupID))
        # img_url = 'https://i.imgur.com/N1pdwVu.png'
        # face = CF.face.detect(img_url)
        faceID = face[0].get('faceId')
        self.logger.info(faceID)
        detection = CF.face.identify([faceID], self.groupID, threshold=0.5)
        self.logger.info(detection)
        candidates = detection[0].get('candidates')
        if len(candidates) > 0:

            bestCandidateID = candidates[0].get('personId')
            bestCandidatePerson = CF.person.get(self.groupID, bestCandidateID)
            bestCandidateName = bestCandidatePerson.get('name')
            self.textToSpeech.say('It is so nice to see you here, ' + str(bestCandidateName) + '. What can I do for you?')
        else :
            self.textToSpeech.say('Could not identify you based on your looks.')
        
    def takePhoto(self):
        time.sleep(0.1)
        self.photoCapture.setCameraID(0)
        self.photoCapture.setResolution(2)
        self.photoCapture.setPictureFormat('jpg')
        fileName = self.photoCapture.takePicture(self.photoPath, 'test'+str(time.time()))
        return str(fileName[0])
        
if __name__ == "__main__":

    app = qi.Application(sys.argv)
    app.start()
    service_instance = SopraSteriaGreeter(app)
    service_id = app.session.registerService(service_instance.service_name, service_instance)
    service_instance.start_app()
    app.run()
    service_instance.cleanup()
    app.session.unregisterService(service_id)
