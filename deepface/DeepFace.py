import matplotlib.pyplot as plt
from keras.preprocessing import image
import warnings
warnings.filterwarnings("ignore")
import time
import os
import numpy as np
import pandas as pd
from tqdm import tqdm
import json

#from basemodels import VGGFace, OpenFace, Facenet, FbDeepFace
#from extendedmodels import Age, Gender, Race, Emotion
#from commons import functions, distance as dst

from deepface.basemodels import VGGFace, OpenFace, Facenet, FbDeepFace
from deepface.extendedmodels import Age, Gender, Race, Emotion
from deepface.commons import functions, distance as dst

def verify(img1_path, img2_path=''
	, model_name ='VGG-Face', distance_metric = 'cosine', plot = False):
	
	tic = time.time()
	
	if type(img1_path) == list:
		bulkProcess = True
		img_list = img1_path.copy()
	else:
		bulkProcess = False
		img_list = [[img1_path, img2_path]]
		
	#------------------------------
	
	if model_name == 'VGG-Face':
		print("Using VGG-Face model backend and", distance_metric,"distance.")
		model = VGGFace.loadModel()
		input_shape = (224, 224)	
	
	elif model_name == 'OpenFace':
		print("Using OpenFace model backend", distance_metric,"distance.")
		model = OpenFace.loadModel()
		input_shape = (96, 96)
	
	elif model_name == 'Facenet':
		print("Using Facenet model backend", distance_metric,"distance.")
		model = Facenet.loadModel()
		input_shape = (160, 160)
	
	elif model_name == 'DeepFace':
		print("Using FB DeepFace model backend", distance_metric,"distance.")
		model = FbDeepFace.loadModel()
		input_shape = (152, 152)
	
	else:
		raise ValueError("Invalid model_name passed - ", model_name)
	
	#------------------------------
	
	#tuned thresholds for model and metric pair
	threshold = functions.findThreshold(model_name, distance_metric)
	
	#------------------------------
	resp_objects = []
	for instance in img_list:
		if type(instance) == list and len(instance) >= 2:
			img1_path = instance[0]
			img2_path = instance[1]
			
			#----------------------
			
			if os.path.isfile(img1_path) != True:
				raise ValueError("Confirm that ",img1_path," exists")
			
			if os.path.isfile(img2_path) != True:
				raise ValueError("Confirm that ",img2_path," exists")
			
			#----------------------
			#crop and align faces
			
			img1 = functions.detectFace(img1_path, input_shape)
			img2 = functions.detectFace(img2_path, input_shape)
			
			#----------------------
			#find embeddings
	
			img1_representation = model.predict(img1)[0,:]
			img2_representation = model.predict(img2)[0,:]
			
			#----------------------
			#find distances between embeddings
			
			if distance_metric == 'cosine':
				distance = dst.findCosineDistance(img1_representation, img2_representation)
			elif distance_metric == 'euclidean':
				distance = dst.findEuclideanDistance(img1_representation, img2_representation)
			elif distance_metric == 'euclidean_l2':
				distance = dst.findEuclideanDistance(dst.l2_normalize(img1_representation), dst.l2_normalize(img2_representation))
			else:
				raise ValueError("Invalid distance_metric passed - ", distance_metric)
			
			#----------------------
			#decision
			
			if distance <= threshold:
				identified =  "true"
			else:
				identified =  "false"
			#----------------------
			if plot:
				label = "Verified: "+identified
				label += "\nThreshold: "+str(round(distance, 2))
				label += ", Max Threshold to Verify: "+str(threshold)
				label += "\nModel: "+model_name
				label += ", Similarity metric: "+distance_metric
				
				fig = plt.figure()
				fig.add_subplot(1,2, 1)
				plt.imshow(img1[0][:, :, ::-1])
				plt.xticks([]); plt.yticks([])
				fig.add_subplot(1,2, 2)
				plt.imshow(img2[0][:, :, ::-1])
				plt.xticks([]); plt.yticks([])
				fig.suptitle(label, fontsize=17)
				plt.show(block=True)
				
			#----------------------
			#response object
			
			resp_obj = "{"
			resp_obj += "\"verified\": "+identified
			resp_obj += ", \"distance\": "+str(distance)
			resp_obj += ", \"max_threshold_to_verify\": "+str(threshold)
			resp_obj += ", \"model\": \""+model_name+"\""
			resp_obj += ", \"similarity_metric\": \""+distance_metric+"\""
			resp_obj += "}"
			
			resp_obj = json.loads(resp_obj) #string to json
			
			if bulkProcess == True:
				resp_objects.append(resp_obj)
			else:
				return resp_obj
			#----------------------
			
		else:
			raise ValueError("Invalid arguments passed to verify function: ", instance)
		
	#-------------------------
	
	toc = time.time()
	
	#print("identification lasts ",toc-tic," seconds")
	
	if bulkProcess == True:
		return resp_objects

def analyze(img_path, actions= []):
	
	if type(img_path) == list:
		img_paths = img_path.copy()
		bulkProcess = True
	else:
		img_paths = [img_path]
		bulkProcess = False
	
	#---------------------------------
	
	#if a specific target is not passed, then find them all
	if len(actions) == 0:
		actions= ['emotion', 'age', 'gender', 'race']
	
	print("Actions to do: ", actions)
	
	#---------------------------------
	
	if 'emotion' in actions:
		emotion_model = Emotion.loadModel()
	
	if 'age' in actions:
		age_model = Age.loadModel()
	
	if 'gender' in actions:
		gender_model = Gender.loadModel()
	
	if 'race' in actions:
		race_model = Race.loadModel()
	#---------------------------------
	
	resp_objects = []
	for img_path in img_paths:
		
		if type(img_path) != str:
			raise ValueError("You should pass string data type for image paths but you passed ", type(img_path))
		
		if os.path.isfile(img_path) != True:
			raise ValueError("Confirm that ",img_path," exists")
		
		resp_obj = "{"
		
		#TO-DO: do this in parallel
		
		pbar = tqdm(range(0,len(actions)), desc='Finding actions')
		
		action_idx = 0
		#for action in actions:
		for index in pbar:
			action = actions[index]
			pbar.set_description("Action: %s" % (action))
			
			if action_idx > 0:
				resp_obj += ", "
			
			if action == 'emotion':
				emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
				img = functions.detectFace(img_path, (48, 48), True)
				
				emotion_predictions = emotion_model.predict(img)[0,:]
				
				sum_of_predictions = emotion_predictions.sum()
				
				emotion_obj = "\"emotion\": {"
				for i in range(0, len(emotion_labels)):
					emotion_label = emotion_labels[i]
					emotion_prediction = 100 * emotion_predictions[i] / sum_of_predictions
					
					if i > 0: emotion_obj += ", "
					
					emotion_obj += "\"%s\": %s" % (emotion_label, emotion_prediction)
				
				emotion_obj += "}"
				
				emotion_obj += ", \"dominant_emotion\": \"%s\"" % (emotion_labels[np.argmax(emotion_predictions)])
				
				resp_obj += emotion_obj
				
			elif action == 'age':
				img = functions.detectFace(img_path, (224, 224), False) #just emotion model expects grayscale images
				#print("age prediction")
				age_predictions = age_model.predict(img)[0,:]
				apparent_age = Age.findApparentAge(age_predictions)
				
				resp_obj += "\"age\": %s" % (apparent_age)
				
			elif action == 'gender':
				img = functions.detectFace(img_path, (224, 224), False) #just emotion model expects grayscale images
				#print("gender prediction")
				
				gender_prediction = gender_model.predict(img)[0,:]
				
				if np.argmax(gender_prediction) == 0:
					gender = "Woman"
				elif np.argmax(gender_prediction) == 1:
					gender = "Man"
				
				resp_obj += "\"gender\": \"%s\"" % (gender)
				
			elif action == 'race':
				img = functions.detectFace(img_path, (224, 224), False) #just emotion model expects grayscale images
				race_predictions = race_model.predict(img)[0,:]
				race_labels = ['asian', 'indian', 'black', 'white', 'middle eastern', 'latino hispanic']
				
				sum_of_predictions = race_predictions.sum()
				
				race_obj = "\"race\": {"
				for i in range(0, len(race_labels)):
					race_label = race_labels[i]
					race_prediction = 100 * race_predictions[i] / sum_of_predictions
					
					if i > 0: race_obj += ", "
					
					race_obj += "\"%s\": %s" % (race_label, race_prediction)
				
				race_obj += "}"
				race_obj += ", \"dominant_race\": \"%s\"" % (race_labels[np.argmax(race_predictions)])
				
				resp_obj += race_obj
			
			action_idx = action_idx + 1
		
		resp_obj += "}"
		
		resp_obj = json.loads(resp_obj)
		
		if bulkProcess == True:
			resp_objects.append(resp_obj)
		else:
			return resp_obj
	
	if bulkProcess == True:
		return resp_objects

def detectFace(img_path):
	img = functions.detectFace(img_path)[0] #detectFace returns (1, 224, 224, 3)
	return img[:, :, ::-1] #bgr to rgb

#---------------------------

functions.initializeFolder()

#---------------------------
