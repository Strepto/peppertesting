# -*- coding: utf-8 -*-
"""
Created on Fri Apr 07 15:48:44 2017

@author: ahugo
"""

import cognitive_face as CF
import os
import glob
import time

groupID = 1337
KEY = '6125152da7554bca93dba66b0da57699'
CF.Key.set(KEY) 


personsPath = os.path.dirname(os.path.relpath(__file__))

personsListInAzure = CF.person.lists(groupID)
#print personsListInAzure

#for person in personsListInAzure:
#    pid  = person.get('personId')
#    CF.person.delete(groupID, pid)
#    time.sleep(6)
#    print "deleted" + str(person.get('name'))

namesInAzure = [str(person.get('name').lower()) for person in personsListInAzure]
print namesInAzure

files = glob.glob('D:/Profiles/nhals/OneDrive - Sopra Steria/Nils Henrik Hals/Pepper Robot/SteriaGreeterDebug/SteriaGreeterDebug/utils/photo/*')
print files
for filePath in files:
    if filePath.endswith(".png") or filePath.endswith(".jpg"):
        personInfo = filePath.split('\\').pop()
        personInfo = personInfo.split(' ')
        personNameList = [personInfo[i] for i in range(1, len(personInfo)-1)]
        personName = ' '.join(personNameList) + ' ' + str(personInfo[0])
        if str.lower(personName) not in namesInAzure:
            personCreated =  CF.person.create(groupID, personName)
            personID = personCreated.get('personId')
            print filePath
            CF.person.add_face(filePath, groupID, personID)
            print 'person created: ' + personName
            time.sleep(6)
        else:
            print 'Person already in Azure ' + personName    

print "Scanning directory ended and photos added."
print "Training Azure..."
CF.person_group.train(groupID)
print "Done!"
print "Program Completed."

