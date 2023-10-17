import os
import sys
import json

from binaryhelper import BinaryStream

from pvdb import readPHDC,writePHDC,getPHDC_Size,readTDB,writeTDB,createDBV,zipJson

def read(file_path):
    ret = {}
    with open(file_path,"rb") as f:
        bs=BinaryStream(f)
        #MAGIC_HEAD
        bs.readInt64()
        bs.readCString(4)
        bs.readInt32()
        bs.readInt64()
        db_ver=bs.readInt32()
        #READ_PHDC
        ret["PHDC"]=readPHDC(bs)
        #READ_HASH_OF_PHDC
        ddi_hash=bs.readCString(260)
        #BLOCK_SPLIT
        bs.readInt32() #ALWAYS 2
        #BLOCK_TDB
        ret["TDB"]=readTDB(bs)
        #BLOCK_DBV
        ret["DBV"]=createDBV(bs,ret["PHDC"])
    return ret

def DDIFileToJson(DDI_file_path,json_file_path):
    data = read(DDI_file_path)
    ziped = zipJson(data)
    with open(json_file_path,"w") as f:
        json.dump(ziped,f)
