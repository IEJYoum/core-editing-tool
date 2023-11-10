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
#import gpt1 as gpt
#import czi_tma_scene_position_12 as ctsp
import torch
import matplotlib.pyplot as plt
import string
import math
import mpld3

#from flask import Flask, request, render_template
app = Flask(__name__)
app.secret_key ="123"

SAVE = False
TEST = True

class Session1:
    def __init__(self,di):
        self.di = di
    def put(self,key,val):
        self.di[key] = val
    def get(self,key):
        try:
            return(self.di[key])
        except:
            return(None)
    def clear(self):
        self.di = {}

session1 = Session1(di={})        



@app.route('/',methods =["GET","POST"])
def mmenu(): 
    if not session1.get('data'):
        session1.clear()
        op=[]
        st=[]
        return(redirect(url_for('getData')))
    else:
        print('co data')
        data = session1.get('data')
        df = load()
        print(df)
        if type(df) == str:
            session1.clear()
            print("clearing session, starting fresh")
            return(render_template("done.html"))
        
        print(int(session1.get('nrw')))
        returns = getRM(df.iloc[:,0:2],df.iloc[:,2]) #CREATES fig.html
        rna = ['xs','ys','names','coreID','htens','vtens']
        for i,r in enumerate(returns):
            #print(r,type(rna[i]))
            session1.put(rna[i],r)
        return redirect(url_for("edit"))
    #return render_template('menu.html')
    #return render_template('menu.html',op=op,showText=st,data=session.get('data'))

@app.route('/getData',methods =["GET","POST"])
def getData():
    print("geting data")
    if request.method == 'POST':
        print("post")
        data = request.form.get('data')
        nr = request.form.get('nrw')
        nc = request.form.get('ncl')
        session1.put('data', data)
        session1.put('nrw', int(nr))
        session1.put('ncl', int(nc))
        print(session1.get('data'),"data in getdata post!")
        print(type(data))
        
        return redirect(url_for("mmenu"))
    if request.method == 'GET':  
        print("get")
        return render_template("getData1.html")
    
@app.route('/edit',methods =["GET","POST"])
def edit():
    print(session1.get('coreID'),'ids 0')
    if request.method == 'POST':
        intid = request.form.get('intid')
        gridid = request.form.get('gridid')
        nam = session1.get('names')
        ids = session1.get('coreID')
        #print(ids,"ids 1")
        done = request.form.get("done")
        audience = request.form.get("menuc")
        #print(intid,gridid)
        try:
            nind = nam.index(int(intid))
            
        except:
            try:
                nind = nam.index(intid)
            except:
                print("sorry, index not found")
                if done == "1":
                    print("saving and moving on")
                    return redirect(url_for("save"))
                return redirect(url_for("edit"))
        ids[nind] = gridid
        session1.put('gridid',ids)
        session1.put('coreID', ids) #what here is redundant... 
        #print(ids,"ids 2")
        coords = pd.DataFrame([session1.get('xs'),session1.get('ys')]).transpose()
        tensors = [session1.get('htens'),session1.get('vtens')]
        showOut(coords,nam,ids,tensors,title="")
        #print(ids,"ids 3")
        #print(session.get('coreID'),'ids 4')
        if done == "1":
            print("redirecting to getdata")
            return redirect(url_for("save"))
    return render_template("edit.html")


@app.route('/save',methods =["GET","POST"])
def save():
    nam = session1.get('names')
    ids = session1.get('coreID')
    data = session1.get("data")
    rnd = session1.get("R")
    rounds = session1.get("rounds")
    df = pd.read_csv(data,index_col=0).astype(str)
    if 'coremap' not in list(df.columns):
        df['coremap'] = ''
    key = df.loc[:,"round"] == rnd
    #print(nam,ids)
    sdf = df.loc[key,:]
    #print(sdf.loc[:,"names"])
    diiit = list(sdf.loc[:,"names"])[0]
    #print(diiit,type(diiit))
    for i in range(len(nam)):
        N,I = nam[i],ids[i]
        #print(type(N),N,I,"N","I")
        nkey = sdf.loc[:,"names"] == str(N)
        print(nkey.sum(),'nks')
        sdf.loc[nkey,'coremap'] = I
    df.loc[key,:] = sdf
    df.to_csv(data)
    
    
    rounds.append(rnd)
    session1.put("rounds",rounds)  #done saved rounds
    return(redirect(url_for("mmenu")))
    
def load():
    data = session1.get("data")
    df = pd.read_csv(data,index_col=0).astype(str)
    rounds = session1.get("rounds")
    if type(rounds) != list:
        rounds = []
        session1.put("rounds", rounds)
    for rd in sorted(list(df.loc[:,"round"].unique())):
        if rd not in rounds:
            key = df.loc[:,"round"] == rd
            sdf = df.loc[key,:]
            session1.put("R", rd)
            if "coremap" in list(sdf.columns):
                if list(sdf.loc[:,'coremap'])[0] != "nan":
                    session1.put('coreID', list(sdf.loc[:,'coremap']))
            return(sdf)
    return("done")
    

def getRM(coords,names,title=''):   
    print(coords,names)
    coords = coords.astype(float)
    xs,ys = coords.iloc[:,0],coords.iloc[:,1]
    mxs = [min(xs),max(xs)]
    mys = [min(ys),max(ys)]
    print(mxs,type(mxs),"before settensor")
    tensors = setTensors(mxs,mys)
    lloss = 999999999999999
    optim = torch.optim.SGD(tensors[0]+tensors[1],lr=1e-3) #gradients big gd since no b
    #optim2 = torch.optim.SGD(tensors[1],lr=1e-4)
    i = 0
    reps = 0
    if type(session1.get('coreID')) == type(None):
        while True:
            try:
                i += 1
                inters = getInters(tensors)
                if i == 1:
                    show(inters,xs,ys)
                coreID,allD = findClosest(coords,inters)
                #if i == 1:
                    #print(allD)
                loss = sum(allD)
                if loss < lloss:
                    #
                    loss.backward()
                    optim.step()
                    print(float((loss-lloss).detach()),"delta loss -")
    
                    lloss = loss
                    if TEST:
                        break
                else:
                    reps += 1
                    if reps > 0 and i > 10:
                        break
    
                    loss.backward()
                    optim.step()
                    print(float((loss-lloss).detach()),"delta loss +")
    
            except KeyboardInterrupt:
                print(i,"iters!")
                break
        show(inters,xs,ys)
    else:
        coreID = session1.get('coreID')
    showOut(coords,names,coreID,tensors,title=title)
    #ok the last thing to do is make all rounds in one csv with all cores a1 a2 a3 as index r1 r2 as columns
    rets = []
    for var in [xs,ys,names,coreID]:
        try:
            rets.append(list(var))
        except:
            print(type(var),"tyvar")
            rets.append(list(var.detach()))
    
    h,v = [],[]    
    dire = [h,v]
    for i in range(2):
        ten = tensors[i]
        for j in range(len(ten)):
            nt = []
            ntl = list(ten[j].detach())
            for var in ntl:
                nt.append(float(var.detach()))
            dire[i].append(nt)
        
    rets += dire    
    print("np returnin rets")    
    return(rets)

def showOut(coords,names,coreID,tensors,title=""):
    print("multiply M by scaling ratio!!!")

    fig = plt.figure(figsize=(int(session1.get('ncl'))/5,int(session1.get('nrw'))/5),dpi=500)
    mco = coords.min(axis=0)
    coords = coords - mco
    Mco = coords.max(axis=0)
    coords = coords/Mco
    #mx,my = coords.iloc[i,0].min(),coords.iloc[i,1].min()
    for i in range(len(coords)):
        x,y = coords.iloc[i,0],coords.iloc[i,1]
        #print(x,y,coreID[i])
        plt.scatter(x,y,s=3)
        #print(names,"names")
        #print(i,type(i))
        plt.text(x,y,str(coreID[i])+" "+str(list(names)[i]))
        #print(coords.iloc[i,:],coreID[i])
    for i in range(2):
        for ten in tensors[i]:
            m = 0
            try:
                b = (float(ten[1].detach()) - mco[1-i])/Mco[1-i]
            except:
                b = (ten[1]- mco[1-i])/Mco[1-i]
            y0 = -.1 * m + b
            y1 = 1.1*m + b
            if i == 0:
                plt.plot([-.1,1.1],[y0,y1],linestyle="dashed",color="lightgray")
            else:
                plt.plot([y0,y1],[-.1,1.1],linestyle="dashed",color="lightgray")
    plt.title(title)
    if SAVE:
        print("not saving")
        #plt.savefig(saveF(0,"coreSortingMaps",title),bbox_inches='tight')
    mpld3.save_html(fig,'templates/fig.html')
    plt.show()
    #render_template("fig.html")

def saveF(data,foln,filn,typ="png"):
    badS = [':']
    for bs in badS:
        if bs in filn:
            filn = filn.replace(":",".")
        if bs in foln:
            foln = foln.replace(":",".")
    if not os.path.isdir(SPATH+"/"+foln):
        if not os.path.isdir(SPATH):
            os.mkdir(SPATH)
        os.mkdir(SPATH+"/"+foln)
    if typ == "png":
        return(SPATH+"/"+foln+"/"+filn+'.png')


def show(inters,xs,ys):
    plt.scatter(xs,ys,s=50)
    plt.scatter(inters.iloc[:,0],inters.iloc[:,1],s=25)
    plt.show()

def findClosest(coords,inters):
    #print("finding closest intersections")
    alphab = list(string.ascii_uppercase)
    #print(alphab)
    allD = []
    coreID = []
    for i in range(coords.shape[0]):
        coord = list(coords.iloc[i,:])
        distances = []
        for j in range(inters.shape[0]):
            inte = list(inters.iloc[j,:])
            #print(coord,inte)
            d = (coord[0] - inte[0])**2 + (coord[1] - inte[1])**2
            distances.append(d)
        md = min(distances)
        allD.append(md)
        minD = distances.index(md)

        #row and column names swapped

        colInd = int(session1.get('nrw')) - (math.floor(minD/int(session1.get('ncl'))))-1
        #colInd = math.floor(minD/int(session.get('ncl')))
        colL = alphab[colInd]

        rowN = (minD % int(session1.get('ncl'))) +1
        rowL = str(rowN)
        if len(rowL) == 1:
            rowL = "0"+rowL
        coreID.append(colL+rowL)

    return(coreID,allD)

def getInters(tensors):
    inters = []
    for hten in tensors[0]:
        diit,b = hten[0],hten[1]
        m = 0 #no gradients happening here
        for vten in tensors[1]:
            diiit,a = vten[0],vten[1]
            n = 0 #no gradients happening here
            x = (a+n*b)/(1-n*m)
            y = m*x+b
            #ycheck = (m*a + b)/ (1- n*m)
            #print(y,ycheck)
            inters.append([x,y])
    inters = pd.DataFrame(inters)
    return(inters)


def setTensors(mxs,mys):
    tensors = [[],[]] #[[horizontal tensors][vertical tensors]] - > [M,B] in mx + b
    colStep = (mxs[1] - mxs[0])/(int(session1.get('ncl'))-1)
    rowStep = (mys[1] - mys[0])/(int(session1.get('nrw'))-1)
    for i in range(int(session1.get('nrw'))):
        b = mys[0] + i * rowStep
        tensors[0].append(torch.tensor([0.0,b],requires_grad = True))
    for i in range(int(session1.get('ncl'))):
        b = mxs[0] + i * colStep
        #print(b)
        tensors[1].append(torch.tensor([0.0,b],requires_grad = True))
    return(tensors)    
    


'''
@app.route('/show',methods =["GET","POST"])
def show():
    data = request.form.get('data')
    session['data'] = data
    print(data,"ding!")
    return render_template('menu.html',op=op,showText=st,data=session.get('data'))
'''    
    

if __name__ == "__main__":
    a = app.run(debug=True, use_reloader=False)
    #print(a)
