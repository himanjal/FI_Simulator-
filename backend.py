from subprocess import *
import subprocess
import tempfile
import time
import untangle


from Tkinter import *


class trigger:
    bp = ""
    lp =""
    regList = []
    mask = ""



class Model:


    faults = []
    cFile = ""
    xmlFile = ""
    topLevel = None
    pluginProcess = None
    tempf = None
    pointer = 0

    def __init__(self, top):
        self.topLevel = top
        self.tempf = tempfile.TemporaryFile()


    def printOutput(self, line):
        print line
        self.topLevel.gdb_table.insert(END, line)



    def populateFaults(self):
        self.faults = []
        for item in self.xmlFile.xml.action:
            newTrigger = trigger()
            newTrigger.regList = []
            for reg in item.rg['registerList'][1:-1].split(','):
                newTrigger.regList.append(reg.split()[0])
            newTrigger.bp = item.bp['breakpointAddress']
            newTrigger.lp = item.lp['loopCounter']
            newTrigger.mask = item.mk['mask']
            self.faults.append(newTrigger)


    def connect(self):
        file = self.cFile
        subprocess.call("arm-linux-gnueabi-gcc -g {0} -o {1}-arm -static".format(file, file.split('.')[0]) , shell=True, stdout=subprocess.PIPE)
        subprocess.call("fuser -n tcp -k 1234", shell=True,stdout=subprocess.PIPE)
        qemuProcess = Popen("qemu-arm -singlestep -g 1234 {0}-arm".format(file.split('.')[0]), shell=True, stdout=subprocess.PIPE)
        #self.printOutput("QEMU launched on port 1234")

        self.pluginProcess = Popen('arm-none-eabi-gdb', stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=self.tempf)
        self.pluginProcess.stdin.write("file {0}-arm\n".format(file.split('.')[0]))
        self.pluginProcess.stdin.write("target remote localhost: 1234\n")
        self.pluginProcess.stdin.write("set pagination off\n")

        #self.printOutput("GDB Connected to QEMU")
        self.readGDB()
        self.addBreakpoints()




    def addBreakpoints(self):

        bpNum = 1
        for trigger in self.faults:
            bp = trigger.bp


            if bp[0:2] == "0x":
                self.pluginProcess.stdin.write("B *" + bp + "\n")
            else: self.pluginProcess.stdin.write("B " + bp + "\n")
            

            self.pluginProcess.stdin.write("ignore " + str(bpNum) + " " + trigger.lp + "\n")
            
            self.pluginProcess.stdin.write("commands\n")
            
            self.pluginProcess.stdin.write("info R\n")
            

            for reg in trigger.regList:
                self.pluginProcess.stdin.write("set $" + reg + "=0\n")
            
            self.pluginProcess.stdin.write("del " + str(bpNum) + "\n")

            # if bpNum == len(faults):
            #     self.pluginProcess.stdin.write("B add\n")
            
            self.pluginProcess.stdin.write("info R\n")

            self.pluginProcess.stdin.write("c\n")

            self.pluginProcess.stdin.write("end\n")

            bpNum = bpNum + 1 
            self.readGDB()
        


    def readReg(self):

    	time.sleep(0.1)
    	self.tempf.seek(self.pointer)
    	line = self.tempf.read()
    	self.pointer = self.tempf.tell()
    	for text in line.split('\n'):
    		row = ""
    		for word in text.split():
    			row = row + word + "\t"
    		self.topLevel.reg_table.insert(END, row)



    def sendCommand(self, line):
    	self.pluginProcess.stdin.write(line + "\n")

    	if line == "info R":
    		self.readReg()
    	else:
    		self.readGDB()




    def readGDB(self):
    	time.sleep(0.1)
        self.tempf.seek(self.pointer)
        for line in self.tempf.read().split('\n'):
            self.printOutput(line)
        self.pointer = self.tempf.tell()


    def importXML(self, fileName):
        self.xmlFile = untangle.parse(fileName)
        self.populateFaults()

    def importCFile(self,fileName):
        self.cFile = fileName

    def getFaults(self):
        return self.faults

def initModel(top):
    model = Model(top)
    return model




