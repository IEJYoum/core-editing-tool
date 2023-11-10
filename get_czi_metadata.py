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


#FOLD = r"\\accsmb.ohsu.edu\CEDAR\ChinData\_Images\AxioScan\AxioScan2.CEDAR\VS-PancTMA and 7015Da"#r
#FOLD = "T:\_Images\AxioScan\AxioScan2.CEDAR\cmIF_2023-04-07_WOO"  #r"T:\_Images\AxioScan\AxioScan2.CEDAR\cmIF_2023-04-07_WOO\2023-04-17_R3"
#FOLD = "T:\_Images\AxioScan\AxioScan2.CEDAR\cmIF_2023-04-07_WOO"
#FOLD = r'T:\_Images\AxioScan\AxioScan2.CEDAR\cmIF_2023-04-07_BCC'
#KEYS = [["VS-TMA-12_2"]]
#KEYS = [["pTMA2-25_2023_04_17"]]
FOLD = r"T:\_Images\AxioScan\AxioScan2.CEDAR\cmIF_2023-10-12_VS-TMA-12 and 7015DA-11"
KEYS = [['VS-TMA-12_2']]

#FILE = "R3_PCNA.CD8.CD4.Ecad_pTMA1-25_2023_04_17__5208.czi"
#FILE = "R3_PCNA.CD8.CD4.Ecad_pTMA2-25_2023_04_17__5209.czi"
#coords = "pTMA1-25_ScenePositions_coor.csv"


NROW,NCOL = 9,12#12,16#


def main():
    allC = []
    for fold in sorted(os.listdir(FOLD)):
        print("trying",fold)
        nF = FOLD+"/"+fold
        if not os.path.isdir(nF):
            continue
        try:
            coords,names = getCoords(nF)
            coords["names"] = names
            coords["round"] = fold

            allC.append(coords)
        except Exception as e:
            print(fold,"no czi?\n",e)
    odf = pd.concat(allC,axis=0)
    odf.to_csv("VStma_nov8_metadata.csv")





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
        sn = int(scene.attrib["Index"])+1 #Id or Index?  Id doesn't work

        names.append(str(sn))
        cp = scene.find('./CenterPosition')
        coord = cp.text.split(",")
        #print(coord)
        coords.append(coord)
    coords = pd.DataFrame(coords,columns=["x","y"],index=names).astype(float)
    coords.loc[:,"y"] *= -1
    print(names)
    print(fold)
    return(coords,names)


if __name__ == "__main__":
    main()