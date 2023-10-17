from struct import *
class BinaryStream:
    def __init__(self, base_stream):
        self.base_stream = base_stream

    def readByte(self):
        return self.base_stream.read(1)
    def readBytes(self, length):
        return self.base_stream.read(length)
    def readChar(self):
        return self.unpack('b')
    def readUChar(self):
        return self.unpack('B')
    def readBool(self):
        return self.unpack('?')
    def readInt16(self):
        return self.unpack('h', 2)
    def readUInt16(self):
        return self.unpack('H', 2)
    def readInt32(self):
        return self.unpack('i', 4)
    def readUInt32(self):
        return self.unpack('I', 4)
    def readInt64(self):
        return self.unpack('q', 8)
    def readUInt64(self):
        return self.unpack('Q', 8)
    def readFloat(self):
        return self.unpack('f', 4)
    def readDouble(self):
        return self.unpack('d', 8)
    def readString(self):
        length = self.readUInt32()
        return self.unpack(str(length) + 's', length).decode()
    def readCString(self,length):        
        return self.unpack(str(length) + 's', length).decode().split('\x00')[0]
    def readTString(self,length):        
        return self.unpack(str(length) + 's', length).decode()
    def readFString(self,length):    
        oba=list(bytearray(self.base_stream.read(length)))
        obb=bytearray(filter(lambda x:x != 255,oba))
        return unpack(str(len(obb)) + 's', obb)[0].decode()

    def readYMHArrayHead(self):
        return {
            "name":self.readFString(12),
            "prm":list(self.readBytes(4)),
            "argc":self.readInt64(),
            "sub_count":self.readInt32()
        }

    def writeBytes(self, value):
        if type(value)==bytearray:
            value = bytes(value)
        self.base_stream.write(value)
    def writeChar(self, value):
        self.pack('c', value)
    def writeUChar(self, value):
        self.pack('C', value)
    def writeBool(self, value):
        self.pack('?', value)
    def writeInt16(self, value):
        self.pack('h', value)
    def writeUInt16(self, value):
        self.pack('H', value)
    def writeInt32(self, value):
        self.pack('i', value)
    def writeUInt32(self, value):
        self.pack('I', value)
    def writeInt64(self, value):
        self.pack('q', value)
    def writeUInt64(self, value):
        self.pack('Q', value)
    def writeFloat(self, value):
        self.pack('f', value)
    def writeDouble(self, value):
        self.pack('d', value)
    def writeString(self, value):
        value=value.encode()
        length = len(value)
        self.writeUInt32(length)
        self.pack(str(length) + 's', value)
    def writeCString(self, value):
        value=value.encode()
        length = len(value)
        self.pack(str(length) + 's', value)    
    def writeTString(self, value, length):
        value=("{0:\x00<"+ f"{length}" +"}").format(value).encode()
        length = len(value)
        self.pack(str(length) + 's', value)
    def writeFString(self, value, length):
        value=bytearray(value.encode())
        value.reverse()
        while len(value)<length:
            value.append(255)
        value.reverse()
        self.writeBytes(value)
    
    def writeYMHArrayHead(self,value):
        self.writeFString(value.get("name",""),12)
        self.writeBytes(bytearray(value.get("prm",[0,0,0,0])))
        self.writeInt64(value.get("argc",1))
        sub_count=value.get("sub_count",0)
        self.writeInt32(sub_count)

    def pack(self, fmt, data):
        return self.writeBytes(pack(fmt, data))
    def unpack(self, fmt, length = 1):
        return unpack(fmt,self.readBytes(length))[0]