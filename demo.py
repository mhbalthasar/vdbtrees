#/bin/env python3

import os
import sys

from pdat import JsonToTxtFile,JsonToDatFile
from ptree import TreeFileToJson,JsonToTreeFile
from pddi import DDIFileToJson

if __name__=="__main__":
    BASE_FOLDER="demo"
    FTREE=os.path.join(BASE_FOLDER,"Luotianyi_CHN_Meng.tree")
    FDAT=os.path.join(BASE_FOLDER,"Luotianyi_CHN_Meng.dat")
    FTXT=os.path.join(BASE_FOLDER,"Luotianyi_CHN_Meng.txt")
    FDDI=os.path.join(BASE_FOLDER,"Luotianyi_CHN_Meng.ddi")
    FJSON=os.path.join(BASE_FOLDER,"Luotianyi_CHN_Meng.json")
    #读取数据
    #途径1：从DDI提取JSON
    DDIFileToJson(FDDI,FJSON)
    #途经2：从TREE提取JSON
    #TreeFileToJson(FTREE,FJSON)
    #写入输出
    JsonToTxtFile(FJSON,FTXT)
    JsonToTreeFile(FJSON,FTREE)
    JsonToDatFile(FJSON,FDAT)