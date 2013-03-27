'''Submit CHARMM jobs remotely'''

import ssh

class RunCharmmRemotely(ssh.RunCommandRemotely):
	'''Run CHARMM job remotely'''
	def __init__(self, server, charmmInp="", subdir=""):
		ssh.RunCommandRemotely.__init__(self, server=server, subdir=subdir)
		self.charmmInp = ""
		self.charmmOut = ""
		self.subjobs   = []

	def generateCharmmJob(self, inpFile, outFile):
		self.charmmInp = inpFile
		self.charmmOut = outFile
		return \
'''#!/bin/bash
#$ -m a
#$ -M %s

input=%s
output=%s
tempdir=%s/$JOB_ID
mkdir -p $tempdir
oridir=%s

cp -r $oridir/* $tempdir/
cd $tempdir
mpirun=%s
charmm=%s
if [  "$NSLOTS" -gt 1 ]; then
  $mpirun -v -np $NSLOTS $charmm < $input > $output
else
    $charmm < $input > $output
fi

cd $oridir
mv $tempdir/* $oridir
rmdir $tempdir
''' % (self.config.get('misc','email'), self.charmmInp, self.charmmOut,
	self.config.get(self.server, 'scratchdir'), self.remdir,
	self.config.get(self.server,'mpirun'),
	self.config.get(self.server, 'charmm'))

	def remoteSimulationTerminatedNormally(self, myFile):
		# Analyze remote simulation output log. Return True if it's reached Normal
		# Termination; False otherwise.
		baseFile = myFile
		if baseFile.find("/") != -1:
			baseFile = myFile[myFile.rfind("/")+1:]
		remFile = self.remdir + "/" + baseFile
		try:
			f = self.sftp.open(remFile,'r')
			s = f.readlines()
			f.close()
		except IOError, e:
			print "I/O Error: {0}".format(e.strerror)
			return False
		if len(s) < 11:
			return False
		for i in range(len(s)-10,len(s)):
			if "NORMAL TERMINATION BY NORMAL STOP" in s[i]:
				return True
		return False

	def consistentAndGet(self, myFile):
		# Analyze remote simulation and get file. Return True if it was
		# successful, False otherwise.
		if self.remoteFileExists(myFile) is False:
			return False
		status = self.remoteSimulationTerminatedNormally(myFile)
		if status == False:
			return False
		self.getFile(myFile)
		return True

if __name__ == "__main__":
	# Testing with verdi
	server = 'verdi'
	rmtChm = RunCharmmRemotely(server, subdir='dir000000')
	print rmtChm.generateCharmmJob(inpFile='sim.inp', outFile='sim.out')
