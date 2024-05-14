from flask import Flask, redirect, url_for, render_template
import subprocess
import os
from llama_cpp import Llama
import random
import csv
import os
import javalang

app = Flask(__name__)

LLM = Llama(model_path="./models/mistral-7b-instruct-v0.1.Q8_0.gguf", n_ctx=2048, n_gpu_layers=5)

directory = "code_files"

@app.route("/")
@app.route('/index')
def index():
	return redirect(url_for('dashboard'))
	# return render_template('test.html')

@app.route('/dashboard')
def dashboard():
	# return redirect(url_for('question'))
	return render_template('dashboard.html')

@app.route('/chapter/<chapter_name>')
def chapter(chapter_name):
	# return redirect(url_for('question'))
	chapter_questions_map = {
		"Operators": [
			["Add Integers", "addIntegers"],
			["Subtract Integers", "subtractIntegers"],
			["Multiply Integers", "multiplyIntegers"],
			["Divide Integers", "divideIntegers"],
			["Get Remainder", "getRemainder"]
		],
		"Strings": [
			["Reverse String", "reverseString"]
		],
		"Arrays": [
			["Find Integer", "findIntegerInArray"]
		]
	}
	return render_template('chapter.html', chapter_name=chapter_name, questions_list = chapter_questions_map[chapter_name])

@app.route('/question/<questionID>')
def question(questionID):
	return render_template('question.html', questionID=questionID)

@app.route('/get_question/<questionID>')
def get_question(questionID):
	print("get question called")
	print(questionID)
	# questionID servers as the function name too
	# questionID = "addIntegers"
	# questionID = "reverseString"
	# questionID = "findIntegerInArray"

	allQuestionPrompts = {
		"addIntegers": {
			"question": "Write a function in java to add 2 integers.", 
			"functionHeader": "public static int add(int a, int b)", 
			"classBodyStart": "public class MyClass {\n\npublic static void main(String args[]) {\n     System.out.println(add(2, 3));System.out.println(add(-1, 3));System.out.println(add(0, 0));\n} \n\n", 
			"expectedOutput": "5\n2\n0", 
			"topic": "Operators"
		},
		"reverseString": {
			"question": "Write a function in java to reverse a string without using StringBuilder.", 
			"functionHeader": "public static String reverseString(String str)", 
			"classBodyStart": "public class MyClass {\n\npublic static void main(String args[]) {\n     System.out.println(reverseString(\"hello\"));\n} \n\n", 
			"expectedOutput": "olleh", 
			"topic": "Strings"
		},
		"findIntegerInArray": {
			"question": "Write a function in java to find an integer in an array.",
			"functionHeader": "public static boolean findIntegerInArray(int arr[], int toFind)",
			"classBodyStart": "public class MyClass {\n\npublic static void main(String args[]) {\n     int arr[] = {3, 6, -1, 7, 5, 8};\n     System.out.println(findIntegerInArray(arr, 5));\n} \n\n",
			"expectedOutput": "true",
			"topic": "Arrays"
		}
	}

	question = allQuestionPrompts[questionID]['question']
	functionHeader = allQuestionPrompts[questionID]['functionHeader']

	prompt = question + " Dont add any comments and use this function header: " + functionHeader

	className = "MyClass"
	classBodyStart = allQuestionPrompts[questionID]['classBodyStart']
	classBodyEnd = "\n\n}"
	expectedOutput = allQuestionPrompts[questionID]['expectedOutput']
	topic = allQuestionPrompts[questionID]['topic']

	# prompt = "Write a function in java to reverse a string without using string builder. Use this function header: public static String reverseString(String str)"
	# functionHeader = "public static String reverseString(String str)"
	# className = "MyClass"
	# classBodyStart = "public class MyClass {\n\npublic static void main(String args[]) {\n     System.out.println(reverseString(\"hello\"));\n} \n\n"
	# classBodyEnd = "\n\n}"
	# expectedOutput = "olleh"
	# topic = "Strings"
	
	# prompt = "Write a function in java to concatenate 2 strings. Use this function header: public static String concat(String a, String b)"
	# functionHeader = "public static String concat(String a, String b)"
	# className = "MyClass"
	# classBodyStart = "public class MyClass {\n\npublic static void main(String args[]) {\n     System.out.println(concat(\"hi\", \"there\"));\n} \n\n"
	# classBodyEnd = "\n\n}"
	# expectedOutput = "hithere"
	# topic = "Strings"

	# prompt = "Write a function in java to find an integer in an array. Use this function header: public static boolean find(int arr[], int toFind). Include the header in the output."
	# functionHeader = "public static boolean find(int arr[], int toFind)"
	# className = "MyClass"
	# classBodyStart = "public class MyClass {\n\npublic static void main(String args[]) {\n     int arr[] = {3, 6, -1, 7, 5, 8};\n     System.out.println(find(arr, 5));\n} \n\n"
	# classBodyEnd = "\n\n}"
	# expectedOutput = "true"
	# topic = "Arrays"

	# prompt = "Write a function in java to add 2 integers. Use this function header: public static int add(int a, int b). Include the header in the output."
	# functionHeader = "public static int add(int a, int b)"
	# className = "MyClass"
	# classBodyStart = "public class MyClass {\n\npublic static void main(String args[]) {\n     System.out.println(add(10, 5));\n} \n\n"
	# classBodyEnd = "\n\n}"
	# expectedOutput = "15"
	# topic = "Operators"

	# infinite loop which executes until correct code is obtained
	generatedCode = ""
	classBodyComplete = ""
	while True:
		generatedCode = get_LLM_response(prompt, functionHeader)
		
		classBodyComplete = classBodyStart + generatedCode + classBodyEnd
		
		isCorrect = check_code_correctness(classBodyComplete, className, expectedOutput)
	
		if isCorrect:
			break
	
	print(classBodyComplete)
	print(generatedCode)
	print(len(generatedCode))

	# for finetuning, save to csv
	save_to_csv_for_finetuning(topic, question, generatedCode)

	allBlanks, choices = insert_blanks(generatedCode, topic, classBodyComplete, questionID)
	print(allBlanks)
	print(choices)
	print(question)

	jsonObject = {
		'topic': topic,
		'question': question,
		'code': generatedCode,
		'allBlanks': allBlanks,
		'choices': choices
	}
	
	return jsonObject

def save_to_csv_for_finetuning(topic, prompt, generatedCode):
	# Ensure the ./finetuning directory exists
    directory = './finetuning'
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Define the CSV file path
    csv_file_path = os.path.join(directory, 'finetuning_data.csv')

    # Open the CSV file in append mode
    with open(csv_file_path, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write the prompt and generated code as a new row in the CSV file
        writer.writerow([topic, prompt, generatedCode])

def get_LLM_response(prompt, functionHeader):
	# create a text prompt
	# prompt = "Write a function in java to reverse a string without using string builder."

	# generate a response (takes several seconds)
	output = LLM(prompt, max_tokens=-1)

	code = output["choices"][0]["text"]

	# cleaning code text
	# print(code.find("`"))
	code = code.replace("```java", "")
	code = code.replace("```", "")

	functionBody = extract_function_body(code, functionHeader)

	# print(functionBody)

	return functionBody

def extract_function_body(code, functionHeader):
	# print(code)
	functionBody = ""

	startIndexOfFunction = code.find(functionHeader)

	if (startIndexOfFunction == -1):
		return functionBody

	stk = [] # append pop
	for i in range(startIndexOfFunction, len(code)):
		# print(code[i])
		if (code[i] == '{'):
			stk.append(code[i])
		elif (code[i] == '}' and len(stk) > 0):
			stk.pop()
			if (len(stk) == 0):
				functionBody += code[i]
				break
		functionBody += code[i]

	return functionBody

def check_code_correctness(classBodyComplete, className, expectedOutput):
	# print(classBodyComplete)

	doesCodeCompile = check_code_compilation(classBodyComplete, className)
	if not doesCodeCompile:
		return False

	isCodeLogicCorrect = check_code_logic(className, expectedOutput)

	return isCodeLogicCorrect

def check_code_compilation(classBodyComplete, className):
	if len(classBodyComplete) == 0:
		return False
	
	# Create the directory if it doesn't exist
	if not os.path.exists(directory):
		os.makedirs(directory)
	
	# Save the Java code to a file within the directory
	fileName = f"{directory}/{className}.java"
	with open(fileName, 'w') as java_file:
		java_file.write(classBodyComplete)
	
	# Compile the Java code
	compile_process = subprocess.run(['javac', fileName], capture_output=True, text=True)
	if compile_process.returncode != 0:
		print(f"Compilation failed with errors:\n{compile_process.stderr}")
		return False

	return True

def check_code_logic(className, expectedOutput):
	# Change to the directory before running to avoid classpath issues
	os.chdir(directory)
	run_process = subprocess.run(['java', className], capture_output=True, text=True)
	os.chdir('..') # Change back to the original directory

	if run_process.returncode != 0:
		print(f"Execution failed with errors:\n{run_process.stderr}")
		return False
	
	# Compare the output
	actualOutput = run_process.stdout
	if actualOutput.strip() == expectedOutput.strip():
		print("Success! The output matches the expected output.")
		return True
	else:
		print("Failure! The output does not match the expected output.")
		print(f"Expected: {expectedOutput.strip()}")
		print(f"Actual: {actualOutput.strip()}")
		return False

def insert_blanks(generatedCode, topic, classBodyComplete, functionName):
	print("inserting blanks")

	blanksDict = {
		"Operators": ["+", "-", "/", "*", "%"],
		"Strings": ["length()", "charAt", "contains", "equals", "StringBuilder"],
		"Arrays": ["length"],
	}

	allBlanks = []
	choices = blanksDict[topic]
	# random.shuffle(choices)

	for i in range(len(choices)):
		keyword = choices[i]
		startIndex = generatedCode.find(keyword)
		if startIndex != -1:
			endIndex = startIndex + len(keyword) - 1

			blank = [startIndex, endIndex, i, -1]
			allBlanks.append(blank)
	

	# if topic == "Strings" or topic == "Arrays":
	# 	insert_blanks_ast(classBodyComplete, topic, allBlanks, functionName)
 
	get_for_loop_blanks(generatedCode, allBlanks, choices)

	remove_overlapping_blanks(allBlanks)

	num_to_pick = min(3, len(allBlanks)) 
	allBlanks = random.sample(allBlanks, num_to_pick)
	
	allBlanks.sort(key=lambda x: x[0]) # sorting all blanks by start index

	index_map = {}
	for i in range(len(choices)):
		index_map[i] = choices[i]
	
	print(index_map)
	
	random.shuffle(choices)

	for blank in allBlanks:
		blank[2] = choices.index(index_map[blank[2]])	
	
	print(allBlanks)

	return (allBlanks, choices)

def get_for_loop_blanks(generatedCode, allBlanks, choices):
	forStartIndex = generatedCode.find("for")

	if forStartIndex == -1:
		return

	forControlStatement = "" # for (.....) the part in the brackets is the control statement
	foundFirstOpenBracket = False
	stk = []
	for i in range(forStartIndex, len(generatedCode)):
		if (generatedCode[i] == '('):
			stk.append(generatedCode[i])
			foundFirstOpenBracket = True
		elif (generatedCode[i] == ')' and len(stk) > 0):
			stk.pop()
			if (len(stk) == 0):
				forControlStatement += generatedCode[i]
				break
		if foundFirstOpenBracket:
			forControlStatement += generatedCode[i]
	
	# removing the start and end bracket
	forControlStatement = forControlStatement[1:]
	forControlStatement = forControlStatement[:len(forControlStatement)-1]

	forControlParts = forControlStatement.split(";")

	for part in forControlParts:
		part = part.strip()
		partIndex = generatedCode.find(part)
		blank = [partIndex, partIndex+len(part)-1, len(choices), -1]
		allBlanks.append(blank)

		choices.append(part)

def remove_overlapping_blanks(allBlanks):
	blanksToRemove = []
	for i in range(len(allBlanks)):
		for j in range(len(allBlanks)):
			if i == j:
				continue
			if allBlanks[i][0] >= allBlanks[j][0] and allBlanks[i][1] <= allBlanks[j][1]:
				blanksToRemove.append(i)
				break
	
	for i in range(len(blanksToRemove), -1):
		allBlanks.pop(blanksToRemove[i])

# def insert_blanks_ast(classBodyComplete, topic, allBlanks, functionName):
# 	# Parse the Java code
# 	tree = javalang.parse.parse(classBodyComplete)

# 	# Traverse the tree
# 	functionFound = False
# 	for path, node in tree:
# 		if type(node) is javalang.tree.MethodDeclaration and node.name==functionName:
# 			functionFound = True

# 		if functionFound:    
# 			# print(type(node), node)
# 			# print(node.position)
# 			# print(path)

# 			if type(node) is javalang.tree.ForStatement:
# 				print("found for statement")
# 				position = find_index_of_node(classBodyComplete, node.position)
# 				print(node.position)
# 				print(position)
# 				print(classBodyComplete[position:position+5])	
# 			# elif type(node) is javalang.tree.BinaryOperation:
# 			# 	print("found binary operation statement")
# 			# 	position = find_index_of_node(classBodyComplete, node.position)
# 			# 	print(node.position)
# 			# 	print(position)
# 			# 	print(classBodyComplete[position:position+5])
# 			elif type(node) is javalang.tree.Assignment:
# 				print("found assignment statement")
# 				position = find_index_of_node(classBodyComplete, node.position)
# 				print(node.position)
# 				print(position)
# 				print(classBodyComplete[position:position+5])
# 			elif type(node) is javalang.tree.MethodInvocation:
# 				print("found method invocation statement")
# 				position = find_index_of_node(classBodyComplete, node.position)
# 				print(node.position)
# 				print(position)
# 				print(classBodyComplete[position:position+5])


# 			# if topic == "Strings":
# 			# 	pass
# 			# elif topic == "Arrays":
# 			# 	pass

# 		if type(node) is javalang.tree.ReturnStatement:
# 			break

# def find_index_of_node(code, position):
#     if position:
#         lines = code.split('\n')
#         line_start = sum(len(lines[i]) + 1 for i in range(position.line - 1))  # +1 for newline characters
#         index = line_start + position.column - 1  # -1 because columns are 1-indexed
#         return index
    # return None




if __name__ == '__main__':
	app.run(debug=True)