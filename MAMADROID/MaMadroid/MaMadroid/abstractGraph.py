#coding=utf-8
import os
from multiprocessing import Process
import shutil
from gml2txt import caller2callee, gml2graph


def _preprocess_graph(app, _dir):
    '''Preprocesses the graph data and calls a custom function for further processing.'''
    # Ensure the output directory exists
    os.makedirs(_dir, exist_ok=True)
    
    # Generate a temporary file path in the specified directory
    appl = os.path.basename(app)
    temp_file_path = os.path.join(_dir, appl)
    
    # Process the original file and write to a new temp file in _dir
    with open(app, 'r') as read_file, open(temp_file_path, 'w') as write_file:
        for line in read_file:
            # Splitting caller and callee(s)
            caller, callees = line.strip().split(" ==> ")
            caller = caller.split(":")[0].replace("<", "")
            callees_list = callees.split(", ")
            
            # Process and write the caller
            write_file.write(caller + "\t")
            
            # Process each callee and write
            for i, callee in enumerate(callees_list):
                clean_callee = callee.split(":")[0].replace("['<", "").replace("<", "").strip()
                if i < len(callees_list) - 1:
                    write_file.write(clean_callee + "\t")
                else:
                    write_file.write(clean_callee + "\n")
    
    # Call the selfDefined function with the path to the new temporary file
    selfDefined(temp_file_path, _dir)


def selfDefined(f, _dir): #f:包含调用者和被调用者的临时文件 _dir：当前目录文件 
# f: Temporary file containing both caller and callee. _dir: Current directory file.	
	''' calls all three modes of abstraction '''
	Package = []
	Family = []
	Class = []
	fl = os.path.basename(f)
	print(f"Processing {fl} ")
	#将自定义的包、家族以及类加入到上面的数组中 #Add custom packages, families, and classes to the array above.
	with open(_dir + "/Packages.txt") as fh:
		for l in fh:
			if l.startswith('.'):
				Package.append(l.strip('\n').lstrip('.'))
			else:
				Package.append(l.strip('\n').strip())
	with open(_dir + "/Families.txt") as fh:
		for l in fh:
			Family.append(l.strip('\n').strip())
	with open(_dir + "/classes.txt") as fh:
		for l in fh:
			Class.append(l.strip('\n').strip())
	ff = abstractToClass(Class, f, _dir) #ff为提取的class的文件 # ff is the file containing the extracted classes.
	os.remove(f)#删除临时文件 # Delete temporary files.
	Package.reverse()
	fam = Process(target = abstractToMode, args=(Family, ff, _dir))
	fam.start()
	pack = Process(target=abstractToMode, args=(Package, ff, _dir))
	pack.start()
	pack.join()


def _repeat_function(lines, P, fh, _sep): #lines：处理过后的对应文件中每一行包含的每一个数据 P：自定义的class文件（相当于一个名单）fh：某一个APP对应的class文件夹中的文件 _sep：制表符
	if lines.strip() in P:  #如果在名单中写入class文件夹中的文件 # If writing files from the class folder into the roster:
		fh.write(lines.strip() + _sep)
	else:    #如果不在名单中 # If not in the roster:
		if "junit." in lines: #对一些特殊字符串的处理 # Handling of special strings.
			return
		if '$' in lines:
			if lines.replace('$', '.') in P:
				fh.write(lines.replace('$', '.') + _sep)
				return
			elif lines.split('$')[0] in P:
				fh.write(lines.split('$')[0] + _sep)
				return
		items = lines.strip().split('.')
		item_len = len(items)
		count_l = 0
		for item in items:
			if len(item) < 3:
				count_l += 1
		if count_l > (item_len / 2):#字符小于3个的大于整体个数的二分之一 就认定为混淆 # Strings with less than 3 characters and more than half of the total count are considered obfuscated.
			fh.write("obfuscated" + _sep)
		else:
			fh.write("self-defined" + _sep) #否则为自定义 # Otherwise, they are considered custom.


def abstractToClass(_class_whitelist, _app, _dir):#_class_whitelist：自定义的class文件 _app:包含调用者和被调用者的临时文件 _dir：当前目录文件 # _class_whitelist: Custom class files_app: Temporary file containing both caller and callee_dir: Current directory file
	''' abstracts the API calls to classes '''
	filename = os.path.basename(_app)
	newfile = _dir + "/class/" + filename
	os.makedirs(os.path.dirname(newfile), exist_ok=True)
	with open(newfile, 'w') as fh:
		with open(_app) as fp:
			for line in fp:
				lines = line.strip('\n').split('\t')
				lines = [jjj for jjj in lines if len(jjj) > 1] # ensures each caller or callee is not a single symbol e.g., $
				num = len(lines)
				for a in range(num): #将得到的class写入class文件夹下的文件中 # Write the obtained classes into files under the class folder.
					if a < num - 1:
						_repeat_function(lines[a], _class_whitelist, fh, "\t")
					else:
						_repeat_function(lines[a], _class_whitelist, fh, "\n")

	return newfile


def abstractToMode(_whitelist, _app, _dir): #_whitelist：自定义的名单 _app：抽象的class文件 _dir：当前文件目录 # _whitelist: Custom whitelist_app: Abstracted class file_dir: Current directory
	''' abstracts the API calls to either package or family '''

	dico = {"org.xml": 'xml', "com.google":'google', "javax": 'javax', "java": 'java', "org.w3c.dom": 'dom', "org.json": 'json',\
 "org.apache": 'apache', "android": 'android', "dalvik": 'dalvik'}
	family = False
	if len(_whitelist) > 15: #通过名单长度判断是family模式还是package模式 然后在对应文件夹创建对应APP对应模式的文件 # Using the length of the whitelist to determine whether it's in family mode or package mode, then create corresponding files in the respective folders for the corresponding app and mode.
		newfile = _dir + "/package/" + _app.split('/')[-1]
	else:
		newfile = _dir + "/family/" + _app.split('/')[-1]
		family = True

	with open(newfile, 'w') as fh:
		with open(_app) as fp:
			for line in fp:
				lines = line.strip('\n').split('\t')
				for items in lines:
					if "obfuscated" in items or "self-defined" in items:
						fh.write(items + '\t')
					else:
						for ab in _whitelist:
							if items.startswith(ab):#通过startwith进行判断 # Using startswith for verification.
								if family: # if True, family, otherwise, package
									fh.write(dico[ab] + '\t')
								else:
									fh.write(ab + '\t')
								break
				fh.write('\n')