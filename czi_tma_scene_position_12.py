# -*- coding: utf-8 -*-
"""
Created on Mon Oct 23 9:26:30 2023

@author: youm
"""

from aicsimageio import AICSImage
import pandas as pd
import os
import torch
import matplotlib.pyplot as plt
import string
import math
print("use cellpose env")

'''
FOLD = r"\\accsmb.ohsu.edu\CEDAR\ChinData\_Images\AxioScan\AxioScan2.CEDAR\VS-PancTMA and 7015Da"#r
FOLD = "T:\_Images\AxioScan\AxioScan2.CEDAR\cmIF_2023-04-07_WOO"  #r"T:\_Images\AxioScan\AxioScan2.CEDAR\cmIF_2023-04-07_WOO\2023-04-17_R3"
KEYS = [["VS-TMA-12_2"]]
KEYS = [["pTMA2-25_2023_04_17__5209"]]
'''
FOLD = r'\\accsmb.ohsu.edu\CEDAR\ChinData\_Images\AxioScan\AxioScan2.CEDAR\cmIF_2023-10-04_KLF4-2'
SPATH = FOLD
KEYS = [["OHSU-TMA-14_23"],['.czi']]
SAVE = True

#FILE = "R3_PCNA.CD8.CD4.Ecad_pTMA1-25_2023_04_17__5208.czi"
#FILE = "R3_PCNA.CD8.CD4.Ecad_pTMA2-25_2023_04_17__5209.czi"
#coords = "pTMA1-25_ScenePositions_coor.csv"


NROW,NCOL = 8,11#12,16#


def main():
    print("IN THIS VERSION, NO GRADIENT TO ROWS, ONLY SHIFT VERT HORIZ")
    roundMap = []
    inds = []
    df = pd.DataFrame()
    for fold in sorted(os.listdir(FOLD)):
        print("trying",fold)
        nF = FOLD+"/"+fold
        if not os.path.isdir(nF):
            continue
        try:
            coords,names,coreID = getRM(nF,title=fold)
            #print(names,coreID)
        except ZeroDivisionError:
            print("no files found in",fold)
            #print(os.listdir(nF))
            #print(fold)
            continue
        for cI in coreID:
            if cI not in inds:
                inds.append(cI)
        RN = fold.split("_")[-1]
        df[RN] = ""
        inds = sorted(inds)

        iinds = []
        for ind in inds:
            if ind not in df.index:
                df.loc[ind] = ""
        #df = df.loc[iinds,:]
        df = df.sort_index()
        df.loc[coreID,RN] = names
        #roundMap.append(dict(zip(names,coreID)))
        #print(dict(zip(names,coreID)))
    #print(roundMap)
    #
    #print(df)
    nkeys = []
    for k in KEYS:
        nkeys.append("-or-".join(k))
    nkey = "_and_".join(nkeys)
    try:
        df.to_csv(FOLD+'/coreSortingMaps/'+nkey+"_core_map_new.csv")
    except Exception as e:
        df.to_csv(nkey+"_core_map.csv")



def getRM(fold,title=""):
    #return(1)
    coords,names = getCoords(fold)
    #coords = coords.sort_values("x")
    #plt.plot(coords, linestyle = "none")
    #coords.plot(linestyle = "none")
    xs,ys = coords.iloc[:,0],coords.iloc[:,1]
    mxs = [min(xs),max(xs)]
    mys = [min(ys),max(ys)]
    tensors = setTensors(mxs,mys)
    lloss = 999999999999999
    optim = torch.optim.SGD(tensors[0]+tensors[1],lr=1e-3) #gradients big gd since no b
    #optim2 = torch.optim.SGD(tensors[1],lr=1e-4)
    i = 0
    reps = 0
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
    showOut(coords,names,coreID,tensors,title=title)
    #ok the last thing to do is make all rounds in one csv with all cores a1 a2 a3 as index r1 r2 as columns
    return(coords,names,coreID)

def showOut(coords,names,coreID,tensors,title=""):
    print("multiply M by scaling ratio!!!")

    fig = plt.figure(figsize=(NCOL,NROW),dpi=500)
    mco = coords.min(axis=0)
    coords = coords - mco
    Mco = coords.max(axis=0)
    coords = coords/Mco
    #mx,my = coords.iloc[i,0].min(),coords.iloc[i,1].min()
    for i in range(len(coords)):
        x,y = coords.iloc[i,0],coords.iloc[i,1]
        #print(x,y,coreID[i])
        plt.scatter(x,y)
        plt.text(x,y,coreID[i]+" "+names[i])
        #print(coords.iloc[i,:],coreID[i])
    for i in range(2):
        for ten in tensors[i]:
            m = 0#float(ten[0].detach())   #MAKES NO GRADIENT
            #print("\n",m)
            b = (float(ten[1].detach()) - mco[1-i])/Mco[1-i]
            y0 = -.1 * m + b
            y1 = 1.1*m + b
            #print(y0,y1,i)
            if i == 0:
                #plt.plot([(-.1,y0),(1.1,y1)])
                plt.plot([-.1,1.1],[y0,y1],linestyle="dashed",color="lightgray")
                #print("px",(-.1,y0),(1.1,y1))
                #print("px",(-.1,y0),(1.1,y1))
            else:
                plt.plot([y0,y1],[-.1,1.1],linestyle="dashed",color="lightgray")
                #plt.plot([(y0,-.1),(y1,1.1)])
                #print("py",(y0,-.1),(y1,1.1))
                #print("py",(y0,-.1),(y1,1.1))

    plt.title(title)
    if SAVE:
        plt.savefig(saveF(0,"coreSortingMaps",title),bbox_inches='tight')
    plt.show()

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

        colInd = NROW - (math.floor(minD/NCOL))-1
        #colInd = math.floor(minD/NCOL)
        colL = alphab[colInd]

        rowN = (minD % NCOL) +1
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
    colStep = (mxs[1] - mxs[0])/(NCOL-1)
    rowStep = (mys[1] - mys[0])/(NROW-1)
    for i in range(NROW):
        b = mys[0] + i * rowStep
        tensors[0].append(torch.tensor([0.0,b],requires_grad = True))
    for i in range(NCOL):
        b = mxs[0] + i * colStep
        #print(b)
        tensors[1].append(torch.tensor([0.0,b],requires_grad = True))
    return(tensors)





def getCoords(fold):
    print("D")
    goodF = []
    for file in os.listdir(fold):
        #print(file)
        cntr = 0
        for lis in KEYS:
           for item in lis:
               if item in file:
                   cntr += 1
                   continue
        #print(cntr)
        if cntr == len(KEYS):
            goodF.append(file)
    if len(goodF) > 1 :

        for i,fn in enumerate(goodF):
            print(i,fn)
        print("uh oh, multiple files with matching keystrings found")
        ch = int(input("number of correct file?"))
        goodF = [goodF[ch]]
    if len(goodF) == 0:
        1/0

    coords = []
    names = []
    path = fold +"/"+goodF[0]
    im = AICSImage(path)
    meta = im.metadata
    for scene in meta.findall('./Metadata/Information/Image/Dimensions/S/Scenes/Scene'):
        #print(scene.text)
        #print(scene)
        #print(dir(scene))
        #print(scene.attrib["Index"])
        #input('')
        names.append(scene.attrib["Index"]) #Id or Index?  Id doesn't work
        cp = scene.find('./CenterPosition')
        coord = cp.text.split(",")
        #print(coord)
        coords.append(coord)
    coords = pd.DataFrame(coords,columns=["x","y"]).astype(float)
    coords.loc[:,"y"] *= -1
    print(names)
    print(fold)
    return(coords,names)


if __name__ == "__main__":
    main()