from flask import Flask, render_template, request, session
import os
import pymongo
from pymongo import MongoClient
import gridfs
from collections import defaultdict
import base64
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = ""

@app.route('/')
def hello():
    """Return a friendly HTTP greeting."""
    return render_template('index.html')


@app.route('/saving_name', methods=['POST'])
def saving():
    mongo = MongoClient('mongodb://')
    name = request.form['email']
    password = request.form['password']
    mongo.db.userdata.insert({"username": name, "password": password})
    return render_template('index.html')
    mongo.close()


@app.route('/check', methods=['POST'])
def check_presence():
    mongo = MongoClient('mongodb://')
    user = request.form['email']
    password = request.form['password']
    result = mongo.db.userdata.find_one({"username": user}, {"password": 1, "_id": 0})
    print (result)
    if password == result['password']:
        session['username'] = user
        print session['username']
        #session['username'].pop()
        print "Welcome Back!"
        return render_template('output.html')
    else:
        print "Register First"

        mongo.close()
        return render_template('index.html', result=result)


@app.route('/upload_photo', methods=['POST'])
def upload_pic():
    size = 30000000
    mongo = MongoClient('mongodb://')
    db = mongo.db
    fs = gridfs.GridFS(db)
    pic = request.files['file']
    print "taken"
    comment = str(request.form['comment'])
    #return comment
    n = db.photo_count.find_one({"username": session['username']}, {"count": 1, "_id": 0})
    if n:
        num = n['count']
        if num <=5:
            num = num+1
            db.photo_count.update({"username": session['username']},{"$set": {"count": num}})

        else:
            return "Exceeded limit"

    else:
        count = 1
        db.photo_count.insert({"username": session['username'],"count": count})

    s = os.stat(pic.filename)
    photo_size = s.st_size
    if photo_size > size:
        return "file size large"

    pic_no = fs.put(pic, filename=pic.filename)
    db.photos.insert({"username": session["username"], "photoid": pic_no, "comments": comment})
    #db.photos.insert({"username": session["username"], "photoid": pic_no})
    #db.photos.update({"username": session["username"]}, {"$push":{"comments": comment}})

    mongo.close()
    return "success"


@app.route('/show_all_photo', methods=['POST'])
def show_photo():
    mongo = MongoClient('mongodb://')
    db = mongo.db
    fs = gridfs.GridFS(db)
    info = db.photos.find({}, {"username":1, "photoid":1, "comments":1,"_id" :0})
    data = defaultdict(list)
    for find in info:
        ids = find["photoid"]
        name = find["username"]
        comments = find["comments"]
        print ids,comments
        picdata = fs.get(ids).read()
        pic1 = "data:image/jpeg;base64," + base64.b64encode(picdata)
        lists=[]
        lists.append(pic1)
        lists.append(comments)
        data[name].append(lists)

    mongo.close()
    return render_template('photos.html', data=data)


@app.route('/show_my_photo', methods=['POST'])
def show_my_photo():
    mongo = MongoClient('mongodb://')
    db = mongo.db

    name = session["username"]
    info = db.photos.find({"username":name},{"photoid" : 1,"comments":1, "_id":0})
    data = defaultdict(list)
    for find in info:
        ids = find["photoid"]
        comments = find["comments"]
        fs = gridfs.GridFS(db)
        picdata = fs.get(ids).read()
        pic1 = "data:image/jpeg;base64," + base64.b64encode(picdata)
        lists = []
        if comments:
            lists.append(pic1)
            lists.append(comments)
        else:
            lists.append(pic1)
        data[ids].append(lists)

    mongo.close()
    return render_template('MyPics.html',data = data)


@app.route('/delete_photo',methods=['POST'])
def delete_photo():
    mongo = MongoClient('mongodb://')
    db = mongo.db
    fs = gridfs.GridFS(db)
    picid = str(request.form['id'])
    pic_id = ObjectId(picid)

    name = session["username"]
    cnt = db.photo_count.find_one({"username": name}, {"count": 1,"_id": 0})
    print cnt["count"]
    cnt1 = cnt["count"]-1
    db.photo_count.update({"username": name}, {"$set": {"count": cnt1}})

    db.photos.delete_one({"photoid" : pic_id})
    db.fs.files.delete_one({"_id": pic_id})
    db.fs.chunks.delete_one({"files_id": pic_id})

    mongo.close()
    return "deleted"


@app.route('/delete_comment',methods=['POST'])
def delete_comment():
    mongo = MongoClient('mongodb://')
    db = mongo.db
    fs = gridfs.GridFS(db)
    picid = str(request.form['id'])
    pic_id = ObjectId(picid)
    name = session["username"]
    db.photos.update({"photoid": pic_id}, {"$set": {"comments": None}})

    mongo.close()
    return "deleted comment!"

@app.route('/add_comment',methods=['POST'])
def add_comment():
    mongo = MongoClient('mongodb://')
    db = mongo.db
    fs = gridfs.GridFS(db)
    picid = str(request.form['id'])
    pic_id = ObjectId(picid)
    comment = str(request.form['comment'])
    db.photos.update({"username": session["username"]}, {"$push":{"comments": comment}})
    return " ok "


@app.route('/edit_comment',methods=['POST'])
def edit_comment():
    mongo = MongoClient('mongodb://')
    db = mongo.db
    fs = gridfs.GridFS(db)
    picid = str(request.form['id'])
    pic_id = ObjectId(picid)
    ncomment = str(request.form['newcomment'])
    db.photos.update({"photoid": pic_id}, {"$set": {"comments": ncomment}})

    mongo.close()
    return "edited comment!"

if __name__ == '__main__':
    app.run()
# [END app]
