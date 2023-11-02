from flask import Flask, render_template, request, redirect, session, jsonify
import mysql.connector
import os
from tensorflow.keras.models import load_model
import cv2
import numpy as np
import base64
from PIL import Image
import io
import re
import pandas as pd


app=Flask(__name__)
app.secret_key=os.urandom(24)


conn=mysql.connector.connect(host="remotemysql.com", user="VRaKCyqbBz", password="WNElTn61Rk", database="VRaKCyqbBz")
cursor=conn.cursor()


@app.route('/')
def login():
    return render_template("login.html")


@app.route('/register')
def register():
    return render_template("register.html")


@app.route('/home')
def home():
    if 'user_id' in session:
        return render_template("index.html")
    else:
        return redirect('/')


@app.route('/login_validation', methods=['POST'])
def login_validaion():
    email=request.form.get("email")
    password=request.form.get("password")

    cursor.execute("""SELECT * FROM `users` WHERE `email` LIKE '{}' AND `password` LIKE '{}'""".format(email,password))
    users=cursor.fetchall()

    #print(users)

    if len(users)>0:
        session['user_id']=users[0][0]
        return redirect('/home')
    else:
        return redirect('/')


@app.route('/add_user', methods=['POST'])
def add_user():
    name=request.form.get('uname')
    email=request.form.get('uemail')
    password=request.form.get('upassword')

    cursor.execute("""INSERT into `users` (`user_id`, `name`, `email`, `password`) VALUES (NULL,'{}','{}','{}')""".format(name,email,password))
    conn.commit()

    cursor.execute("""SELECT * from `users` WHERE `email` LIKE '{}'""".format(email))
    myuser=cursor.fetchall()
    session['user_id']=myuser[0][0]

    return redirect('/home')


def home():
    return render_template("index.html")



#######################################################################

img_size=100

model=load_model('model/model-015.model')
label_dict={0:'Covid19 Negative', 1:'Covid19 Positive'}
name_list=[]
aadhar_list=[]
result_list=[]
accuracy_list=[]

def preprocess(img):

	img=np.array(img)

	if(img.ndim==3):
		gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
	else:
		gray=img

	gray=gray/255
	resized=cv2.resize(gray,(img_size,img_size))
	reshaped=resized.reshape(1,img_size,img_size)
	return reshaped


@app.route("/predict", methods=["POST"])
def predict():
	print('HERE')
	message = request.get_json(force=True)
	encoded = message['image']
	decoded = base64.b64decode(encoded)
	dataBytesIO=io.BytesIO(decoded)
	dataBytesIO.seek(0)
	image = Image.open(dataBytesIO)

	name=message['name']
	aadhar=message['aadhar']

	test_image=preprocess(image)

	prediction = model.predict(test_image)
	result=np.argmax(prediction,axis=1)[0]
	accuracy=float(np.max(prediction,axis=1)[0])

	label=label_dict[result]

	print(prediction,result,accuracy)

	name_list.append(name)
	aadhar_list.append(aadhar)
	accuracy_list.append(accuracy)
	result_list.append(result)

	response = {'prediction': {'result': label,'accuracy': accuracy}}

	return jsonify(response)


@app.route("/export", methods=["POST", "GET"])
def export():
	m1 = pd.DataFrame({'Name':name_list})
	m2 = pd.DataFrame({'Aadhar No.':aadhar_list})
	m3 = pd.DataFrame({'Result':result_list})
	m4 = pd.DataFrame({'Probability':accuracy_list})

	result = pd.concat([m2,m1,m3,m4],axis=1)

	result.fillna("--",inplace=True)
	result.to_csv("predictions.csv",index=False)
	return render_template("index.html")



#######################################################################


@app.route("/track-button")
def track():
    return render_template("index_tracker.html")


@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect('/')
    

if __name__=="__main__":
    app.run(debug=True)

