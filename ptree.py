import os
import sys
import json

from binaryhelper import BinaryStream

from pvdb import readPHDC,writePHDC,getPHDC_Size,readTDB,writeTDB,readDBV,writeDBV,zipJson,unZipJson

data={}


def read(file_path):
    ret = {}
    with open(file_path,"rb") as f:
        bs=BinaryStream(f)
        #MAGIC_HEAD
        magic_head=bs.readYMHArrayHead()
        if magic_head["prm"]!=[0,0,0,0]:
            ret["prm"]=magic_head["prm"]
        
        #BLOCK_PHDC
        #PHDC_HEAD
        ret["PHDC"]=readPHDC(bs)

        bs.readInt32() #BLOCK_TYPE_SPLIT
        #BLOCK_TDB
        #TDB_HEAD
        ret["TDB"]=readTDB(bs)
        

        #DBV_BLOCK
        ret["DBV"]=readDBV(bs)
        
                
    return ret
def write(file_path,data):
    with open(file_path,"wb") as f:
        bs=BinaryStream(f)
        
        #MAGIC_HEAD
        bs.writeYMHArrayHead({"name":"DBS ",
                              "prm":data.get("prm",[0,0,0,0]),
                              "sub_count":3
                              })#3BLOCK is PHDC,TDB,DBV
        
        #BLOCK_PHDC
        writePHDC(bs,data["PHDC"])

        bs.writeInt32(2)#BLOCK_TYPE_SPLIT
        #BLOCK_TDB
        #TDB_HEAD
        writeTDB(bs,data["TDB"],data["PHDC"])

        #BLOCK_DBV
        #DBV_HEAD
        writeDBV(bs,data["DBV"])
        

def TreeFileToJson(tree_file_path,json_file_path):
    data = read(tree_file_path)
    ziped = zipJson(data)
    with open(json_file_path,"w") as f:
        json.dump(ziped,f)

def JsonToTreeFile(json_file_path,tree_file_path):
    data = None
    with open(json_file_path,"r") as f:
        data = json.load(f)
    unzip = unZipJson(data)
    write(tree_file_path,unzip)

    
