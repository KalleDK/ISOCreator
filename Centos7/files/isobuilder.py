#!/usr/bin/env python

from __future__ import print_function
import os, sys, errno, shutil
import requests
import hashlib
from subprocess import Popen, PIPE

class Progress:
	def __init__(self, divider=0, indent=0, linebreak=0):
		self.divider = divider
		self.indent = indent
		self.linebreak = linebreak
		self.linecounter = 0
		self.counter = 0
		
	def reset(self):
		self.counter = 0
		self.linecounter = 0
		
	def done(self):
		print("")
	
	def next(self):
		self.counter += 1
		if self.counter > self.divider:
			if self.linecounter == 0:
				print(' ' * self.indent, end='')
			
			print('.', end="")
			self.counter = 0
			
			self.linecounter += 1
			if self.linecounter >= self.linebreak:
				self.linecounter = 0
				print("")
				
			sys.stdout.flush()

def silentremove(filename):
	try:
		shutil.rmtree(filename)
	except OSError as e: # this would be "except OSError, e:" before Python 2.6
		if e.errno == errno.ENOENT: # errno.ENOENT = no such file or directory
			pass
		elif e.errno == errno.ENOTDIR: # Not a directory
			os.remove(filename)
		else:
			raise # re-raise exception if a different error occured	
			
def query_yes_no(question, default="yes"):
	"""Ask a yes/no question via raw_input() and return their answer.

	"question" is a string that is presented to the user.
	"default" is the presumed answer if the user just hits <Enter>.
		It must be "yes" (the default), "no" or None (meaning
		an answer is required of the user).

	The "answer" return value is True for "yes" or False for "no".
	"""
	valid = {"yes": True, "y": True, "ye": True,
			 "no": False, "n": False}
	if default is None:
		prompt = " [y/n] "
	elif default == "yes":
		prompt = " [Y/n] "
	elif default == "no":
		prompt = " [y/N] "
	else:
		raise ValueError("invalid default answer: '%s'" % default)

	while True:
		sys.stdout.write(question + prompt)
		choice = raw_input().lower()
		if default is not None and choice == '':
			return valid[default]
		elif choice in valid:
			return valid[choice]
		else:
			sys.stdout.write("Please respond with 'yes' or 'no' "
							 "(or 'y' or 'n').\n")

def download(url, file):
	r = requests.get(url, stream=True)
	progress = Progress(divider=1, indent=2, linebreak=60)
	with open(file, 'wb') as f:
		for chunk in r.iter_content(chunk_size=1024 * 1024): 
			if chunk: # filter out keep-alive new chunks
				f.write(chunk)
				f.flush()
				progress.next()
	progress.done()

def extractISO(iso, source, dest):
	cmd = [
		'/usr/bin/xorriso',
		'-indev', iso,
		'-osirrox', 'on',
		'-extract',
		source,
		dest,
	]
	p = Popen(cmd, stdout=PIPE, stderr=PIPE)
	output, err = p.communicate()
	if p.returncode != 0:
		raise ("ISO","Can't extract " + source)
	
def findISO(iso, path, file):
	cmd = [
		'/usr/bin/xorriso',
		'-indev', iso,
		'-find', path,
		'-name', file,
	]
	p = Popen(cmd, stdout=PIPE, stderr=PIPE)
	output, err = p.communicate()
	if output == '':
		raise("ISO","Couldn't find " + file)
	return output

	
class ISO:
	def __init__(self):
		self.name       = os.environ.get('CUSTOM_ISO') or "CentOS-7-Custom.iso"
		self.base       = os.environ.get('BASE_ISO')   or "CentOS-7-x86_64-Minimal-1503-01.iso"
		self.mirror     = os.environ.get('MIRROR')	   or "http://mirror.one.com/centos/7/isos/x86_64"
		self.sha1       = os.environ.get('SHA1')       or "7c1e34e95c991175290d704dbdcc6531774cbecb"
		self.prettyname = os.environ.get('NAME')       or "CentOS 7 Custom"
		self.cache  = "/buildcache"
		self.dir	= "/iso"
		self.data	= "/data"
		
	def verifyChecksum(self):
		SHA1Hash = hashlib.sha1()
		progress = Progress(divider=1, indent=2, linebreak=60)
		with open(self.dir + "/" + self.base, 'rb') as f:
			while True:
				data = f.read(16 * 1024 * 1024)
				if not data:
					break
				SHA1Hash.update(data)
				progress.next()
		progress.done()		
		return SHA1Hash.hexdigest() == self.sha1
		
	def getBase(self):
		print("")
		print("Getting Base ISO")
		print("==================================")
		print("")
		print("  MIRROR = " + self.mirror)
		print("  ISO    = " + self.base)
		print("")
		if os.path.isfile(self.dir + "/" + self.base):
			print("  ISO exists, validating SHA1")
			if self.verifyChecksum():
				print("  ISO Valid, using local")
				return True
			else:
				print("  ISO Invalid, redownloading")
				silentremove(self.dir + "/" + self.base)
		print("  Downloading ISO")
		download(self.mirror + "/" + self.base, self.dir + "/" + self.base)
		print("  Validating SHA1")
		if self.verifyChecksum():
			print("  ISO Valid")
		else:
			print("  ISO Invalid")
			raise("ISO", "Checksum error")
	
	def clearCache(self):
		print("")
		print ("Clearing Cache folder")
		print ("==================================")
		print("")
		for node in os.listdir(self.cache):
			print("  " + node)
			silentremove(self.cache + "/" + node)
		print("  Done")
			
	def makeSkel(self):
		self.getBase()
		self.clearCache()
		print ("")
		print("Creating Skeleton")
		print ("==================================")
		print ("  ")
		
		file = "isolinux"
		print ("  Extracting /" + file)
		extractISO(self.dir + "/" + self.base, "/isolinux", self.cache + "/" + file)
		
		files = [
			".discinfo",
			"images",
			"LiveOS",
			"Packages",
		]
		for file in files:		
			print ("  Extracting /" + file)
			extractISO(self.dir + "/" + self.base, "/" + file, self.cache + "/isolinux/" + file)
		
		file = findISO(self.dir + "/" + self.base, "/repodata/", "*comps.xml").replace("'", "").strip()
		print ("  Extracting " + file)
		extractISO(self.dir + "/" + self.base, file, self.cache + "/comps.xml")
		
		print("  Creating Repo")
		cmd = [
			'/usr/bin/createrepo',
			'-g', self.cache + "/comps.xml",
			self.cache + "/isolinux",
		]
		p = Popen(cmd, stdout=PIPE, stderr=PIPE)
		output, err = p.communicate()
		
		print("  Fixing permission on isolinux.bin")
		os.chmod(self.cache + "/isolinux/isolinux.bin", 0644)
		
	def build(self):
		if not os.path.isdir(self.cache + "/isolinux"):
			self.makeSkel()
		print("")
		print("Building " + self.name)
		print("==============================")
		print("")
		for node in os.listdir(self.data):
			print("  Copying " + node)
			src = self.data + "/" + node
			dst = self.cache + "/isolinux/" + node
			silentremove(dst)
			if os.path.isdir(src):
				shutil.copytree(src, dst)
			else:
				shutil.copy(src, dst)
				
		print("  Building ISO")
		cmd = [
			'/usr/bin/mkisofs',
			'-o', self.dir + "/" + self.name,
			'-b', 'isolinux.bin',
			'-c' 'boot.cat',
			'-no-emul-boot',
			'-V', self.prettyname,
			'-boot-load-size', '4',
			'-boot-info-table',
			'-R', '-J', '-v',
			'-T', self.cache + '/isolinux'
		]
		p = Popen(cmd, stdout=PIPE, stderr=PIPE)
		output, err = p.communicate()
		print("  Done")
		print("")
			
iso = ISO()

if sys.argv[1] == "clear":
	iso.clearCache()
if sys.argv[1] == "build":
	iso.build()
if sys.argv[1] == "rebuild":
	iso.clearCache()
	iso.build()



		