import os
import sys
import json

from binaryhelper import BinaryStream
from pvdb import readPHDC,writePHDC,getPHDC_Size,zipJson,unZipJson
data={}

def read(file_path):
    ret = {}
    with open(file_path,"rb") as f:
        bs=BinaryStream(f)
        #MAGIC_HEAD
        bs.readCString(4)
        bs.readInt32()
        bs.readInt64()
        #READ_PHDC
        ret["PHDC"]=readPHDC(bs)
    return ret

def write(file_path,data):
    with open(file_path,"wb") as f:
        bs=BinaryStream(f)
        #DEFINE
        MagicSize = 16
        PhdcSize = getPHDC_Size(data["PHDC"])        
        file_size=MagicSize + PhdcSize
        
        #MAGIC_HEAD
        bs.writeCString("DBS ")
        bs.writeInt32(file_size)
        bs.writeInt64(1)

        #WRITE_PHDC
        writePHDC(bs,data["PHDC"])        

def PHDCtoTxt(file_path,data):
    PGrp=data["PHDC"]["Groups"]
    with open(file_path,"wb") as f:
        bs=BinaryStream(f)
        bs.writeCString("# version 1")
        bs.writeBytes(b'\x0d\x0a')
        bs.writeCString("# Generate 2023")
        #--------START-------------
        for pType in PGrp.keys():
            phonemes=PGrp[pType]["phonemes"]
            voiced=PGrp[pType]["voiced"]
            pVoiced="true" if voiced else "false"
            bs.writeBytes(b'\x0d\x0a')
            bs.writeBytes(b'\x0d\x0a')
            titleStr=f"phonetic_group(name=\"{pType}\", voiced={pVoiced}):"
            bs.writeCString(titleStr)
            for c in phonemes:
                bs.writeBytes(b'\x0d\x0a\x09')
                bs.writeCString(c)
            



#----- YOU NEED'T USE THIS FUNCTION.THE TREE FILE JSON COULD USE FOR THIS TOO
#def DatFileToJson(dat_file_path,json_file_path):
#    data = read(dat_file_path)
#    ziped = zipJson(data)
#    with open(json_file_path,"w") as f:
#        json.dump(ziped,f)

def JsonToDatFile(json_file_path,dat_file_path):
    data = None
    with open(json_file_path,"r") as f:
        data = json.load(f)
    unzip = unZipJson(data)
    write(dat_file_path,unzip)


def JsonToTxtFile(json_file_path,txt_file_path):
    data = None
    with open(json_file_path,"r") as f:
        data = json.load(f)
    PHDCtoTxt(txt_file_path,data)

