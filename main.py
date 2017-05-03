#!/usr/bin/env python
# pylint: disable=locally-disabled, fixme, line-too-long, C0111, C0325
import sys
sys.path.append("/home/nao/.local/share/PackageManager/apps/")
import os
import qi
import cognitive_face as CF
import time



class PythonAppMain(object):

    GROUP_ID = 1337
    KEY = '6125152da7554bca93dba66b0da57699'
    BASE_PHOTO_PATH = '/home/nao/recordings/cameras/'
    def __init__(self, application):
        # Getting a session that will be reused everywhere
        self.application = application
        self.session = application.session
        self.service_name = self.__class__.__name__
        # Getting a logger. Logs will be in
        # /var/log/naoqi/servicemanager/{application id}.{service name}
        self.logger = qi.Logger(self.service_name)
        # Do some initializations before the service is registered to NAOqi
        self.logger.info("Initializing...")
        # Insert init functions here
        self.logger.info("Initialized!")
        # Connect to services
        self.connect_services()

    #Connecting to used services.
    @qi.nobind
    def connect_services(self):
        # connect all services required by your module
        # done in async way over 30s,
        # so it works even if other services are not yet ready when you start your module
        # this is required when the service is autorun as it may start before other modules...
        self.logger.info('Connecting services...')
        self.services_connected = qi.Promise()
        services_connected_fut = self.services_connected.future()

        # get services
        def get_services():
            try:
                self.logger.info('Starting Getting Services')
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
            except RuntimeError as ex:
                self.logger.warning('Still missing some service:\n {}'.format(ex))

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
        self.logger.info("Starting app!")
        self.create_signals()
        # Establishing signal listeners
        self.start_dialog()
        self.peoplePerception.setMaximumDetectionRange(1.5)
        self.peoplePerception.justArrived.connect(self.new_person_detected)
        #        self.faceDetected_signal = self.memory.subscriber("FaceDetected").signal
        #        self.faceDetected_signal.connect(self.recognizePerson())
        #        self.faceDetection.learnFace('tempFace'+str(time.time())
        #        self.memory.insertData("SopraSteriaGreeter/tempFace", 10)
        # @TODO: insert whatever the app should do to start
        self.logger.info("Started!")
        print "Started"

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
        self.stop_dialog()
        # @TODO: insert cleaning functions here
        self.logger.info("Cleaned!")

    @qi.nobind
    def create_signals(self):
        found_candidate_event = "sopraSteriaGreeter/bestCandidateName"
        self.memory.declareEvent(found_candidate_event)
        self.logger.info("Event created!" + found_candidate_event)


    @qi.nobind
    def start_dialog(self):
        self.logger.info("Loading dialog")
        dir_path = os.path.dirname(os.path.realpath(__file__))
        topic_path = os.path.realpath(os.path.join(dir_path, "greeterDialog", "greeterDialog_enu.top"))
        self.logger.info("File is: {}".format(topic_path))
        try:
            self.dialog.setLanguage("English")

            with open(topic_path, 'r') as myfile:
                data = myfile.read()
                self.loaded_topic = self.dialog.loadTopicContent(data)
            self.dialog.activateTopic(self.loaded_topic)
            self.dialog.subscribe(self.service_name)
            self.logger.info("Dialog loaded!")
        except Exception, e:
            print "Error while loading dialog: ", e
            self.logger.info("Error while loading dialog: {}".format(e))

    @qi.nobind
    def stop_dialog(self):
        self.logger.info("Unloading dialog")
        try:
            self.dialog.unsubscribe(self.service_name)
            # self.dialog.deactivateTopic("/tmp/tmp.top")
            # self.dialog.unloadTopic("/tmp/tmp.top")
            self.dialog.deactivateTopic(self.loaded_topic)
            self.dialog.unloadTopic(self.loaded_topic)
            self.logger.info("Dialog unloaded!")
        except Exception, ex:
            self.logger.info("Error while unloading dialog: {}".format(ex))

    @qi.nobind
    def new_person_detected(self, num_people):
        self.textToSpeech.say('Hi there. Look me in the eyes please, I\'ll see if I can remember you.')
        self.learn_face(num_retries=2)

    @qi.nobind
    def learn_face(self, num_retries=1):
        if(num_retries > 0):
            is_face_learned = self.faceDetection.learnFace(str(time.time()))
            self.logger.info(is_face_learned)
            if is_face_learned:
                self.recognize_person()
            else:
                self.textToSpeech.say('Hmmmm, i cant really see your face yet.')
                self.learn_face(num_retries-1)

        else:
            self.textToSpeech.say('Hide and come back for another try!')


    @qi.nobind
    def recognize_person(self):
        self.textToSpeech.say('You look great today.')
        CF.Key.set(self.KEY)

        # # When running on Pepper, we should use the local photos taken.
        photo_file_path = self.take_photo()
        self.logger.info("Photo taken and stored at: " + str(photo_file_path))
        face = CF.face.detect(photo_file_path)

        # When running on PC, ignore the Photo stuff and check through an online image.
        # face = CF.face.detect("https://i.imgur.com/hgErMru.png")


        ## Instantiatin a new person thing
        # self.logger.info(CF.person_group.create(groupID, "Pepper"))
        # asmund = CF.person.create(self.groupID, "AAsmund Pedersen Hugo")
        # # asmund = CF.person.get(groupID, '8d11e6d0-1163-4adc-a271-b66e315d9277')
        # asmundID = asmund.get('personId')
        # self.logger.info(CF.person.add_face('https://i.imgur.com/hgErMru.png', self.groupID, asmundID))
        # self.logger.info(CF.person_group.train(self.groupID))
        ##
        if(len(face) > 0):
            face_id = face[0].get('faceId')
            self.logger.info(face_id)
            detection = CF.face.identify([face_id], self.GROUP_ID, threshold=0.5)
            self.logger.info(detection)
            candidates = detection[0].get('candidates')
            if len(candidates) > 0:
                self.textToSpeech.say('it\'s at the tip of my tongue')
                best_candidate_id = candidates[0].get('personId')
                best_candidate_person = CF.person.get(self.GROUP_ID, best_candidate_id)
                best_candidate_name = best_candidate_person.get('name')
                self.memory.raiseEvent('greeterdebug-12321/bestCandidateName', best_candidate_name)
                with open(photo_file_path) as _file:
                    _file.name = _file.name + "-identified"

            else:
                self.textToSpeech.say('Could not identify you based on your looks. Are you sure that I know you?')
        else:
            self.textToSpeech.say('Could not get a good enough look at you.')

    @qi.nobind
    def take_photo(self):
        # Timeout because camera can be occupied by the event we listen for.
        time.sleep(0.1)
        self.photoCapture.setCameraID(0)
        self.photoCapture.setResolution(2)
        self.photoCapture.setPictureFormat('jpg')
        file_name = self.photoCapture.takePicture(self.BASE_PHOTO_PATH, 'greeterPhoto' + str(time.time()))
        return str(file_name[0])


if __name__ == "__main__":
    # with this you can run the script for tests on remote robots
    # run : python main.py --qi-url 123.123.123.123
    APP = qi.Application(sys.argv)
    APP.start()
    SERVICE_INSTANCE = PythonAppMain(APP)
    SERVICE_ID = APP.session.registerService(SERVICE_INSTANCE.service_name, SERVICE_INSTANCE)
    SERVICE_INSTANCE.start_app()
    APP.run()
    SERVICE_INSTANCE.cleanup()
    APP.session.unregisterService(SERVICE_ID)
