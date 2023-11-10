# -*- coding: utf-8 -*-
"""
Created on Sat Oct 28 19:48:10 2023

@author: youm
"""


import pandas as pd
import numpy as np
import random
import time
from flask import Flask, render_template, request, redirect, session, url_for #save_user,
#import chat9 as cha
import gpt1 as gpt

#from flask import Flask, request, render_template
app = Flask(__name__)
app.secret_key ="123"

MAPSIZE = 100


NAME = None
PW = None

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    pA = pd.read_csv("players.csv",index_col=0)
    session["taken"] = False
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        desc = request.form.get('description')
        if name in list(pA.loc[:,"name"]):
            session["taken"] = True
            return redirect(url_for('signup'))
        else:
            #print(pA.columns)
            piL = [name,password,desc,"none",[50,0],100,-1]
            piS = pd.DataFrame([piL],columns = pA.columns)
            #print(piS)
            pA = pd.concat([pA,piS],axis=0)
            pA.index = list(pA.loc[:,'name'])
            pA.to_csv("players.csv")
            session["username"] = name
            #print(session.get('username'),"session get username s")
            return redirect(url_for('mmenu'))

    return render_template('signup.html',taken=session.get('taken'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    #if session.get('logged_in'):
    #    return redirect(url_for('mmenu'))
    pA = pd.read_csv("players.csv",index_col=0)
    if request.method == 'POST':
        name = request.form.get('name')
        if name not in list(pA.loc[:,"name"]):
            session.clear()
            session["message"] = "no user with matching name found" 
            print("redirecting..? user")
            return(redirect(url_for("login")))
        key = pA.loc[:,"name"] == name
        pas = pA.loc[key,"password"].iloc[0]
        des = pA.loc[key,"description"].iloc[0]
        img = pA.loc[key,"image"].iloc[0]
        password = request.form.get('password')
        #print(pas)
        #print(password)
        if str(pas) != str(password):
            #print(str(pas) == str(password))
            session.clear()
            session["message"] = "wrong password!"
            #print("redirecting..? pass")
            return(redirect(url_for("login")))
        else:
            session["username"] = name
            session["description"] = des
            session["image"] = img
            #print(session.get('username'),"session get username l")
            return redirect(url_for('mmenu'))

    return render_template('login.html',message = session.get("message"))



@app.route('/',methods =["GET","POST"])
def mmenu(): 
    if not session.get('username'):
        #print("no username!")
        session.clear()
        op=[]
        st=[]
    else:
        pA,mA,piL,D,op,functions,st,cind,room = initiate()
        #ch0 = 999
        if request.method == 'POST':
            #print(room.loc[:,"entities"],"entites in")
            ch0 = request.form['choice']
            
            print(ch0,'choice')
            audience = request.form.get("menuc")
            print(audience,"audience")
            D["coords"] = piL[cind]
            pA.loc[D["name"],:] = D.values()
            
            switch = -1
            try:
                ch = int(ch0)
                if ch >= len(op):
                    1/0
                switch = 0
            except:
                ch = ch0
                switch = 1
                
            if switch == 0:   
                
                pA,mA,piL=functions[ch](pA,mA,piL)  
                print(piL[cind],"coords!")
                
                #leave room
                ents = []
                for e in list(room.loc[:,"entities"]):
                    if type(e) != dict:
                        continue
                    if e["name"] != session.get("username"):
                        #print(e["name"],session.get("username"),'enti')
                        if type(e) == dict:
                            ents.append(e)
                room = saveRoom(room.loc[:,"description"],
                         room.loc[:,'info'],
                         ents,
                         room.loc[:,"chat"],
                         D)
                
                #update player coordinates         
                D["coords"] = piL[cind]
                pA.loc[D["name"],:] = D.values()
                pA.to_csv("players.csv")
                
                #reload world
                pA,mA,piL,D,op,functions,st,cind,room = initiate()
                st = narrateRoom(room)
                st.append(parsePiL(piL,pA))
    
            elif switch == 1:
                rc = list(room.loc[:,"chat"])
                rc.append(D["name"]+": "+ch0)
                room = saveRoom(room.loc[:,"description"],
                         room.loc[:,'info'],
                         room.loc[:,'entities'],
                         rc,
                         D)
                if int(audience) == 1:
                    ochat = gpt.reply_to_chat(room)
                    if ochat:
                        rc = list(room.loc[:,"chat"])
                        rc.append("Spirit"+": "+ochat)
                room = loadRoom(D,mA)
                for nc in list(room.loc[:,'chat']):
                    if nc not in rc:
                        rc.append(nc)
                room = saveRoom(room.loc[:,"description"],
                         room.loc[:,'info'],
                         room.loc[:,"entities"],
                         rc,
                         D)
                st = narrateRoom(room)
                st.append(parsePiL(piL,pA))

     
    print(session.get('username'),"session get username")
    return render_template('menu.html',op=op,showText=st,user_name=session.get('username'))

def initiate():
    try:
        pA,mA = load()
    except:
        pA,mA,diit = create()
    mA = mA.astype(int)
    piL = list(pA.loc[session.get("username"),:])
    cind = list(pA.columns).index("coords")
    #print(piL)
    #print(piL[cind])
    piL[cind] = parseCoo(piL[cind])

        
    D = dict(zip(pA.columns,piL))
    room = loadRoom(D, mA)
    #print(room,"room")
    st = narrateRoom(room)
    op1 =  ["North","East","South","West"]
    functions1 = [gN,gE,gS,gW]
    op = []
    functions = []
    for i,desc in enumerate(st[2:6]):
        #print(st[2:6])
        if "there is the fence" not in desc:
            #print(op1[i])
            op.append(op1[i])
            functions.append(functions1[i])
    for i in range(len(op)):
        op[i] = str(i)+" "+op[i]
    #print(op)
    return(pA,mA,piL,D,op,functions,st,cind,room)
    
def create(n=0,nn=9,nnn=9):
    print("making new world!!")
    cols = ["name","password","description","image","coords","health","coins"]
    data = [["test","1234","blue ghost","none",[50,0],100,-1],
            ["test2","1234","red knight","none",[50,0],100,-1]]
    pA = pd.DataFrame(data = data,columns=cols)
    #print(list(pA.loc[:,"name"]))
    pA.index = list(pA.loc[:,"name"])
    pA.to_csv("players.csv")
    coor = np.arange(0,MAPSIZE)
    mA = pd.DataFrame(columns=coor,index=coor)
    mA = mA.fillna(0)
    mA.to_csv("map.csv")
    print(pA)
    #print(mA)
    return(pA,mA,9)    

def parsePiL(piL,pA):
    st = []
    for i,pi in enumerate(piL):
        if type(pi) == list or type(pi) == tuple:
            pi2 = ""
            for j in pi:
                pi2 += str(j)+" "
            pi = pi2
        elif type(pi) != str:
            pi = str(pi)
        #print(pi)
        try:
            pi = str(pA.columns[i]) +": "+pi
        except:
            print("ok something funkey")
            pi = "strange unknown: "+pi
        st.append(pi)
    return(st)
        

def parseCoo(cs):
    if type(cs) == list:
        return(cs[0],cs[1])
    #print(cs,"cs")
    c =''
    for ch in cs:
        if ch ==",":
            c+=","
        else:
            try:
                c += str(int(ch))
            except:
                pass
    #print(c)
    cl = c.split(",")
    #print(cl,"coords")
    cl[0],cl[1] = int(cl[0]),int(cl[1])
    return(cl[0],cl[1])

def narrateRoom(room):
    #print(room)
    dirs = ["North ","East ","South ","West "]
    st = []
    ldes = room.loc[:,'description']
    #print(ldes)
    for i,des in enumerate(ldes):
        #print(des,"des")
        #des = des[0]
        if i == 0:
            continue
        elif i == 1:
            st.append(des)
            st.append('')
        elif i < 6: 
            j = i-2
            st.append("To the "+dirs[j]+": "+des)
        elif type(des) == str:
            st.append("also: "+des)
            #print
    st.append('')
    for c in list(room.loc[:,'chat']):
        if type(c) == str:
            st.append(c)
    eo = "Currently in this room: "
    for e in list(room.loc[:,"entities"]):
        if type(e) == dict:
            eo += " "+e["name"]
    st.append('')
    st.append(eo)
        
    return(st)

def gN(pA,mA,piL):
    cind = list(pA.columns).index("coords")
    print("going north")
    c0,c1 = piL[cind][0],piL[cind][1]
    c1 += 1
    piL[cind] = [c0,c1]
    return(pA,mA,piL)

def gE(pA,mA,piL):
    cind = list(pA.columns).index("coords")
    print("going east")
    c0,c1 = piL[cind][0],piL[cind][1]
    c0 += 1
    piL[cind] = [c0,c1]
    return(pA,mA,piL)

def gS(pA,mA,piL):
    cind = list(pA.columns).index("coords")
    print("going south")
    c0,c1 = piL[cind][0],piL[cind][1]
    c1 -= 1
    piL[cind] = [c0,c1]
    return(pA,mA,piL)

def gW(pA,mA,piL):
    cind = list(pA.columns).index("coords")
    print("going west")
    c0,c1 = piL[cind][0],piL[cind][1]
    c0 -= 1
    piL[cind] = [c0,c1]
    return(pA,mA,piL)

def loadRoom(D,mA):
    #print(D)
    coords = D["coords"]
    c0,c1 = coords[0],coords[1]
    #print(c0,c1)
    if mA.iloc[c0,c1] == 0:
        mA.iloc[c0,c1] == 9
        #print(mA.shape,("mapshape on loadroom 0"))
        mA.to_csv("map.csv")
        print("you enter a new location (gpt will do this)")

        nears = [[c0,c1+1],
                 [c0+1,c1],
                 [c0,c1-1],
                 [c0-1,c1]]
        ds1 = []
        n2d = []
        for ne in nears:
            switch = 0
            for e in ne:
                if e < 0 or e >= MAPSIZE:
                    ds1.append("there is the fence.")
                    switch = 1
            if switch == 0:
                if mA.iloc[ne[0],ne[1]] != 1:
                    ds1.append(" lies unexplored territory")
                else:
                    fn = str(ne[0])+"_"+str(ne[1])+".csv"
                    nearDF = pd.read_csv(fn,index_col=0)
                    ndesc = nearDF.loc[:,"description"].iloc[0]
                    ds1.append(ndesc)
                    n2d.append(ndesc)
        d1 = gpt.getShort(n2d)
        d2 = gpt.getLong(d1)
        ds = [d1,d2] + ds1
                    
                  
        riL = ["room","none.png"]
        ents = [D]
        chat = []
        #dat = np.array([ds,riL,ents,chat]).dtype(object)
        rDF = saveRoom(ds,riL,ents,chat,D)
        mA.iloc[c0,c1] = 1

        mA.to_csv("map.csv")
        return(rDF)
    else:
        while mA.iloc[c0,c1] == 9:
            print("generating map....")
            time.sleep(1.5)
            mA = pd.read_csv("map.csv",index_col=0).astype(int)   
    
    if mA.iloc[c0,c1] == 1:
        fn = str(c0)+"_"+str(c1)+".csv"
        rDF = pd.read_csv(fn,index_col=0)
        ds = [rDF.loc[:,"description"].iloc[0],rDF.loc[:,"description"].iloc[1]]
        nears = [[c0,c1+1],
                 [c0+1,c1],
                 [c0,c1-1],
                 [c0-1,c1]]
        for ne in nears:
            #print(ne)
            switch = 0
            for e in ne:
                if e < 0 or e >= MAPSIZE:
                    ds.append(" there is the fence.")
                    switch = 1
            if switch == 0:
                if mA.iloc[ne[0],ne[1]] != 1:
                    ds.append(" lies unexplored territory")
                else:
                    fn = str(ne[0])+"_"+str(ne[1])+".csv"
                    nearDF = pd.read_csv(fn,index_col=0)
                    ds.append(nearDF.loc[:,"description"].iloc[0])
        #rDF = rDF.insert(rDF.shape[0],"entities",D)
        ents = list(rDF.loc[:,"entities"])
        
        rDF = saveRoom(ds,rDF.loc[:,'info'],ents,rDF.loc[:,"chat"],D)
        return(rDF)

def saveRoom(ds,riL,ents,chat,D):
    print('make saveroom load room as 1st step')
    coords = D["coords"]
    c0,c1 = coords[0],coords[1]
    
    nchat = []
    #print(chat,"saving room!")
    for c in chat:
        #print(c,type(c))
        if type(c) == str:
            nchat.append(c)
            #print(c,"nchat!")
    nents = []
    nname = []
    nents.append(D)
    nname.append(D['name'])
    for e in list(ents):
        if type(e) == dict:
            if e['name'] not in nname:
                nname.append(e['name'])
                nents.append(e)
    fn = str(c0)+"_"+str(c1)+".csv"
    rDF1 = pd.read_csv(fn,index_col=0)
    for e in list(rDF1.loc[:,"entities"]):
        if type(e) == dict:
            if e['name'] not in nname:
                nname.append(e['name'])
                nents.append(e)
    
    
    print("saving room",nents)
        
    dat = [ds,riL,nents,nchat]
    ndat = []
    for d in dat:
        ndat.append(list(d))
    dat = ndat
    #print(dat,"dat!")

    rDF = pd.DataFrame(dat)
    rDF = rDF.transpose()
    columns = ["description","info","entities","chat"]
    rDF.columns = columns
    
    rDF.to_csv(fn)
    return(rDF)

def load():
    pA = pd.read_csv("players.csv",index_col=0)
    #print(pA)
    mA = pd.read_csv("map.csv",index_col=0).fillna(0).astype(int)
    #print("ok map shape",mA.shape)
    return(pA,mA)

    



'''
@app.route('/', methods=['POST'])
def my_form_post():

    return ch
'''

'''
def getInput():
    #if request.method == 'POST':
        op = ["create new world (deletes old)","sign up","log in"]
        for i in range(len(op)):
            op[i] = str(i)+" "+op[i]
        choice = request.form.get('choice')
        #choice = request.form['choice']
        print(choice,"choice!")
        return render_template('menu.html',op=op)
'''



if __name__ == "__main__":
    a = app.run(debug=True, use_reloader=False)
    #print(a)
