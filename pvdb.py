import os
import sys
import json
import copy

from binaryhelper import BinaryStream

def readPHDC(bs):
    ret={}
    #PHDC_HEAD
    bs.readCString(4)
    bs.readInt32()
    bs.readInt32()
    #PHDC_ARRAY
    phdc_phoneme_size=bs.readInt32()
    ret["Phonemes"]=[]
    for i in range(0,phdc_phoneme_size):
        ret["Phonemes"].append({
                "phonetic":bs.readCString(30),
                "voiced":not bs.readBool()
            })
    #PHDC_PHG2
    bs.readCString(4)
    bs.readInt32()
    phg2_group_size=bs.readInt32()  
    ret["Groups"]={}
    for i in range(0,phg2_group_size):
        #READ_GROUP_NAME
        group_name = bs.readString()
        group_value_size = bs.readInt32()
        group_total_index = bs.readInt32()
        #READ_GROUP_ITEMS
        ret["Groups"][group_name]=[]
        for j in range(0,group_value_size):
                phonetic_name = bs.readString()
                phonetic_index = bs.readInt32()                    
                ret["Groups"][group_name].append(phonetic_name)
    
    #BLOCK_FIX_COL_PAIR
    EPR_BLOCK_SIZE=bs.readInt32() #BLOCK_PER_100Bytes
    ret["DefEpR"]=[]
    for i in range(0,EPR_BLOCK_SIZE):
        #100Char
        Epr_Item_Phonetic=bs.readCString(32) #Char_Name
        Epr_Item_Count=bs.readInt32()
        Epr_Item={
                "phonetic":Epr_Item_Phonetic,
                "data":[]
        }
        for j in range(0,Epr_Item_Count):            
            Item1=(bs.readInt16(),bs.readInt16())    
            Item2=(bs.readInt16(),bs.readInt16())    
            Item3=(bs.readInt16(),bs.readInt16())    
            Item4=(bs.readInt16(),bs.readInt16())
            Epr_Item["data"].append([
                    Item1,Item2,Item3,Item4
                ])
        ret["DefEpR"].append(Epr_Item)
    return ret

def getPHDC_Size(data,block="total"):
    Phg2Size = 12
    for phg_k in data["Groups"].keys():
        Phg2Size = Phg2Size + len(phg_k) + 12
        for phg_v in data["Groups"][phg_k]:
            Phg2Size = Phg2Size + 8 + len(phg_v)
    FixSize = 4 + len(data["DefEpR"]) * 100
    TotalSize = 16 + len(data["Phonemes"])*31 + Phg2Size + FixSize
    if block=="PHG2":
        return Phg2Size
    else:
        return TotalSize

def writePHDC(bs,data):
    PhdcSize=getPHDC_Size(data)
    Phg2Size=getPHDC_Size(data,block="PHG2")
    #PHDC_BLOCK
    bs.writeCString("PHDC")
    bs.writeInt32(PhdcSize)
    bs.writeInt32(4)
    bs.writeInt32(len(data["Phonemes"]))
    for pht in data["Phonemes"]:
        bs.writeTString(pht["phonetic"],30)
        bs.writeBool(not pht["voiced"])

    #PHDC_PHG2
    bs.writeCString("PHG2")
    bs.writeInt32(Phg2Size)
    bs.writeInt32(len(data["Groups"].keys()))
    gp_index = 0
    for phg_k in data["Groups"].keys():
        #WRITE_GROUP_NAME
        group_name=phg_k
        group_data=data["Groups"][group_name]
        bs.writeString(group_name)
        bs.writeInt32(len(group_data))
        bs.writeInt32(gp_index) #SIGN MIN_START
        for phg_i,phg_v in enumerate(group_data):
            bs.writeString(phg_v)
            gp_index=gp_index+1
            if phg_i < len(group_data)-1:
                bs.writeInt32(gp_index)
            else:
                bs.writeInt32(0)            

    #BLOCK_FIX_COLLECTION
    EPR_BLOCK_SIZE=len(data["DefEpR"])
    bs.writeInt32(EPR_BLOCK_SIZE)
    for i in range(0,EPR_BLOCK_SIZE):
        EPR_PHN=data["DefEpR"][i]["phonetic"]
        EPR_DAT=data["DefEpR"][i]["data"]
        bs.writeTString(EPR_PHN,32)
        bs.writeInt32(len(EPR_DAT))
        for j in range(0,len(EPR_DAT)):
            EPR_BRK=EPR_DAT[j]
            while len(EPR_BRK)<4:
                EPR_BRK.append((0,0))
            for hlr in EPR_BRK:
                hlr=list(hlr)
                if len(hlr)<2:
                    hlr=[0,0]
                bs.writeInt16(hlr[0])
                bs.writeInt16(hlr[1])

def readTDB(bs):
    ret={}
    tdb_head=bs.readYMHArrayHead()
    if tdb_head["prm"]!=[0,0,0,0]:
        ret["prm"]=tdb_head["prm"]
                
    #TMM_ARRAY
    ret["TMM"]=[]
    tmm_count=tdb_head["sub_count"]
    for i in range(0,tmm_count):
        tmm={"array":[],"phonetic":""}
        tmm_head=bs.readYMHArrayHead()
        if tmm_head["prm"]!=[0,0,0,0]:
            tmm["prm"]=tmm_head["prm"]
        tmm_keys=bs.readInt32()
        for k in range(0,tmm_keys):
            #ARR_BLOCK_HEAD
            arr_head=bs.readYMHArrayHead()
            tmm_key = bs.readString()
            if arr_head["prm"]==[0,0,0,0]:
                tmm["array"].append({"value":tmm_key})
            else:
                tmm["array"].append({"prm":arr_head["prm"],"value":tmm_key})
        tmm["phonetic"]=bs.readString()            
        ret["TMM"].append(tmm)

    bs.readString()#timbre
    return ret

def writeTDB(bs,data,PHDC_Data):
    phonemes = PHDC_Data["Phonemes"]
    bs.writeYMHArrayHead({"name":"TDB ",
                              "prm":data.get("prm",[0,0,0,0]),
                              "sub_count":len(data["TMM"])
                              })
    #TMM_ARRAY
    for _,tmm in enumerate(data["TMM"]):

        #FIND PHOETIC_TMM IN THE INDEX OF PHONEMES:
        for PHINDEX in range(0,len(phonemes)):
            PHR=phonemes[PHINDEX]
            if PHR["phonetic"]==tmm["phonetic"]:
                break

        bs.writeYMHArrayHead({"name":"TMM ",
                              "prm":tmm.get("prm",[0,0,0,0]),
                              "sub_count":PHINDEX
        })
        bs.writeInt32(len(tmm["array"]))
        for arr in tmm["array"]:
            bs.writeYMHArrayHead({"name":"ARR ",
                              "prm":arr.get("prm",[0,0,0,0]),
                              "sub_count":0
            })
            bs.writeString(arr["value"])
        bs.writeString(tmm["phonetic"])
        
    bs.writeString("timbre")

def readDBV(bs):
    ret={}
    dbv_head=bs.readYMHArrayHead()
    dbr_head=bs.readYMHArrayHead() #WHY
    if dbv_head["prm"]!=[0,0,0,0]:
        ret["prm"]=dbv_head["prm"]
        
    for dbv_i in range(0,dbv_head["sub_count"]):
        bkName=bs.readString()
        if bkName=="voice":
            ret[bkName]={}
            continue
        bkHead=bs.readYMHArrayHead()
        ret[bkName]={"ARR":[]}
        if bkHead["prm"]!=[0,0,0,0]:
            ret[bkName]["prm"]=bkHead["prm"]                    
        for art_i in range(0,max(1,max(bkHead["sub_count"],1))):  
            if bkName=="note":
                ret[bkName]["ARR"].append({"name":"","value":bs.readString()})
                continue
            art_head=bs.readYMHArrayHead() 
            if art_head["name"]=="ART ":
                bs.readBytes(4)#0
            art_index=art_head["sub_count"]
            art_phonetic=bs.readString()
            if art_head["prm"]!=[0,0,0,0]:
                ret[bkName]["ARR"].append({"name":art_head["name"],"prm":art_head["prm"],"value":art_phonetic})
            else:
                ret[bkName]["ARR"].append({"name":art_head["name"],"value":art_phonetic})
    return ret

def createDBV(bs,PHDC_Data):
    phonemes = PHDC_Data["Phonemes"]
    ret={
        "stationary": {
            "ARR": []
        },
        "articulation": {
            "ARR": [
                {
                    "name": "ARR ",
                    "value": "notetonote"
                },
                {
                    "name": "ARR ",
                    "value": "attack"
                },
                {
                    "name": "ARR ",
                    "value": "release"
                }
            ]
        },
        "note": {
            "ARR": [
                {
                    "name": "",
                    "value": "vibrato"
                }
            ]
        },
        "voice": {}
    }    
    for phonetic in phonemes:
        ret["stationary"]["ARR"].append({"name":"ART ","value":phonetic["phonetic"]})
    return ret

def writeDBV(bs,data):
    bs.writeYMHArrayHead({"name":"DBV ",
                          "prm":data.get("prm",[0,0,0,0]),
                          "sub_count":4
                          })
    bs.writeYMHArrayHead({"name":"ARR ",
                          "sub_count":0
                          })
    #DBV_DATA

    dbv_head=["stationary","articulation","note","voice"]
    for bkName in dbv_head:
        if not bkName in data.keys():
            print("Missing", bkName)
            continue
        bs.writeString(bkName)
        if bkName=="voice":
            continue
        bkCount=len(data[bkName]["ARR"])
        bs.writeYMHArrayHead({
                            "name":"ARR ",
                            "prm":data[bkName].get("prm",[0,0,0,0]),
                            "sub_count":bkCount if bkCount>1 else 0
        })
        for art_i in range(0,bkCount):
            art=data[bkName]["ARR"][art_i]
            if bkName=="note":
                bs.writeString(art["value"])
                continue                
            if art["name"]=="ART ":
                bs.writeYMHArrayHead({
                            "name":art["name"],
                            "prm":art.get("prm",[0,0,0,0]),
                            "sub_count":art_i
                })                
                bs.writeInt32(0)
            else:
                if bkName=="articulation":
                    sub_index=0
                else:
                    sub_index=0 if art_i==bkCount-1 else art_i                    
                bs.writeYMHArrayHead({
                            "name":art["name"],
                            "prm":art.get("prm",[0,0,0,0]),
                            "sub_count":sub_index
                })                
            bs.writeString(art["value"])

def zipJson(src):
    data=copy.deepcopy(src)
    ret={}
    AREA=["PHDC","TDB","DBV"]
    for AREA_C in AREA:
        #ZIP_PHDC
        if AREA_C=="PHDC":
            ret["PHDC"]={"Groups":{}}
            ret["PHDC"]["Groups"]={}
            o=data["PHDC"]["Groups"]            
            p=data["PHDC"]["Phonemes"]
            for group_key in o.keys():
                ret_i={"phonemes":[],"voiced":False}
                ov=o[group_key]
                if len(ov)>0:
                    om=ov[0]
                    for pi in p:
                        if pi["phonetic"]==om:
                            ret_i["voiced"]=pi["voiced"]
                            break
                for om in ov:
                    ret_i["phonemes"].append(om)
                ret["PHDC"]["Groups"][group_key]=ret_i
            if len(data["PHDC"]["DefEpR"])>0:
                ret["PHDC"]["DefEpR"]=data["PHDC"]["DefEpR"]
        if AREA_C=="TDB":
            ret["TDB"]={}
            if data["TDB"].get("prm",None)!=None:
                ret["TDB"]["prm"]=data["TDB"]["prm"]
            ziped_TMM={}
            uz_TMM=data["TDB"]["TMM"]
            for ar in uz_TMM:
                is_uz=False
                if ar.get("prm",None)!=None:
                    is_uz=True
                else:
                    for i in ar["array"]:
                        if i.get("prm",None)!=None:
                            is_uz=True
                if is_uz:
                    i=0
                    while i<len(ar["array"]):
                        if ar["array"][i].get("prm",None)==None:
                            del ar["array"][i]
                        else:
                            i=i+1
                    tm_p=ar["phonetic"]
                    del ar["phonetic"]
                    if ar["array"]==[]:
                        del ar["array"]                        
                    else:
                        ar_arr={}
                        for ar_arr_i in ar["array"]:
                            ar_arr[ar_arr_i["value"]]=ar_arr_i["prm"]
                        ar["array"]=ar_arr
                    ziped_TMM[tm_p]=ar
            if ziped_TMM!={}:
                ret["TDB"]["TMM"]=ziped_TMM
            if ret["TDB"]=={}:
                del ret["TDB"]
        if AREA_C=="DBV":
            ret["DBV"]={}
            if data["DBV"].get("prm",None)!=None:
                ret["DBV"]["prm"]=data["DBV"]["prm"]

            zMap=["stationary","articulation","note"]
            for zChar in zMap:
                z_stat={}
                if data["DBV"][zChar].get("prm",None)!=None:
                    z_stat["prm"]=data["DBV"][zChar]["prm"]
                z_stat_arr={}
                for o_arr in data["DBV"][zChar].get("ARR"):
                    o_phon=o_arr["value"]
                    if o_arr.get("prm",None)!=None:
                        z_stat_arr[o_phon]=o_arr["prm"]
                if z_stat_arr!={}:
                    z_stat["ARR"]=z_stat_arr
                if z_stat!={}:
                    ret["DBV"][zChar]=z_stat
            if data["DBV"]["voice"]!={}:
                ret["DBV"]["voice"]=data["DBV"]["voice"]
            if ret["DBV"]=={}:
                del ret["DBV"]
    return ret

def unZipJson(src):
    data=copy.deepcopy(src)
    ret={}
    AREA=["PHDC","TDB","DBV"]
    for AREA_C in AREA:
        #UNZIP_PHDC
        if AREA_C=="PHDC":
            o=data["PHDC"]["Groups"]
            ret["PHDC"]={"Phonemes":[],"Groups":{},"DefEpR":data["PHDC"].get("DefEpR",[])}
            for group_key in o.keys():
                ov=o[group_key]
                ret["PHDC"]["Groups"][group_key]=[]
                for om in ov["phonemes"]:
                    ret["PHDC"]["Groups"][group_key].append(om)
                    ret["PHDC"]["Phonemes"].append({"phonetic":om,"voiced":ov["voiced"]})
        if AREA_C=="TDB":
            ret["TDB"]={}
            data["TDB"]=data.get("TDB",{})
            if data["TDB"].get("prm",None)!=None:
                ret["TDB"]["prm"]=data["TDB"]["prm"]
            ziped_TMM=data["TDB"].get("TMM",{})
            unziped_TMM=[]
            phonemes=ret["PHDC"]["Phonemes"]
            for tmm_i in phonemes:
                if tmm_i["voiced"]:
                    #TMM
                    tmm_p = tmm_i["phonetic"]
                    tmm_o = {"array":[{"value":"pitch"},{"value":"dynamics"},{"value":"opening"}],"phonetic":tmm_p}
                    tmm_c=ziped_TMM.get(tmm_p,None)
                    if tmm_c!=None:
                        if tmm_c.get("prm",None)!=None:
                            tmm_o["prm"]=tmm_c["prm"]
                        tmm_c["array"]=tmm_c.get("array",{})
                        for i in range(0,len(tmm_o["array"])):
                            ttp=tmm_o["array"][i]["value"]
                            if tmm_c["array"].get(ttp,None)!=None:
                                tmm_o["array"][i]["prm"]=tmm_c["array"][ttp]
                    unziped_TMM.append(tmm_o)
            ret["TDB"]["TMM"]=unziped_TMM
        if AREA_C=="DBV":
            ret["DBV"]=createDBV(None,ret["PHDC"])
            data["DBV"]=data.get("DBV",{})
            if data["DBV"].get("prm",None)!=None:
                ret["DBV"]["prm"]=data["DBV"]["prm"]
            zMap=["stationary","articulation","note"]
            for zChar in zMap:
                if data["DBV"].get(zChar,None)!=None:
                    if data["DBV"][zChar].get("prm",None)!=None:
                        ret["DBV"][zChar]["prm"]=data["DBV"][zChar]["prm"]
                    data["DBV"][zChar]["ARR"]=data["DBV"][zChar].get("ARR",{})
                    for i in range(0,len(ret["DBV"][zChar]["ARR"])):
                        pho=ret["DBV"][zChar]["ARR"][i]["value"]
                        if data["DBV"][zChar]["ARR"].get(pho,None)!=None:
                            ret["DBV"][zChar]["ARR"][i]["prm"]=data["DBV"][zChar]["ARR"][pho]
            ret["DBV"]["voice"]=data["DBV"].get("voice",ret["DBV"]["voice"])
    return ret