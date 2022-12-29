import sys
import re
from enum import Enum
import json
import requests

replaceRegularExpression = [
                            ['if\s*\((.*)\)\s*\{', 'if \\1 {'],
#                            ['if\((.*)\)\{', 'if \\1 {'],
                            ['\[NSString stringWithFormat:@*(.*)\]', 'String(format: \\1)'],
                            ['\[(.*) isEqualToString:@*(.*)\]', '\\1 == \\2'],
                            ['NSString \*(.*) = @*(.*);', 'let \\1 = \\2'],
                            ['NSString *\*', 'String'],
                            ['NS', ''],
                            ['CGRectMake\((.*), (.*), (.*), (.*)\)', 'CGRect(x: \\1, y: \\2, width: \\3, height: \\4)'],
                            ['\[(.*) count\]', '\\1.count'],
                            ['BOOL', 'Bool'],
                            ['', ''],
                            ['NO', 'false'],
                            ['YES', 'true'],
                            ['@"(.*)"', '"\\1"'],
                            ['#pragma mark - (.*)', '// MARK: - \\1'],
                            [';', ''],
]

funcReplaceRegularExpression = [
]

    
def mainReplaceFunc(lines, mainFunc, mainStatement, appendlineStatement):
    outputLines = []
    currentLine = ""
    appendLineFlag = False
    for i, line in enumerate(lines):
        if line.startswith("//"):
            continue
        elif appendLineFlag:
            if appendlineStatement(line):
                currentLine = currentLine + line.replace("\n", " ")
                appendLineFlag = True
                continue
            else:
                currentLine = currentLine + line
                appendLineFlag = False
                currentLine = mainFunc(currentLine)
        elif mainStatement(line):
            if appendlineStatement(line):
                currentLine = line.replace("\n", " ")
                appendLineFlag = True
                continue
            else:
                currentLine = line
                appendLineFlag = False
                currentLine = mainFunc(currentLine)
        else:
            currentLine = line
            appendLineFlag = False
        outputLines.append(currentLine)
    return outputLines
    

def replaceOthers(lines):
    outputLines = lines
    for expressions in replaceRegularExpression:
        outputLines = replaceOther(outputLines, expressions[0], expressions[1])
    return outputLines


def replaceOther(lines, regularExpression, replaceStr):
    outputLines = []
    currentLine = ""
    for i, line in enumerate(lines):
        if line.startswith("//"):
            continue
        currentLine = re.sub(regularExpression, replaceStr, line)
        outputLines.append(currentLine)
    return outputLines


def replaceComment(lines):
    outputLines = []
    currentLine = ""
    for i, line in enumerate(lines):
        if line.startswith("//"):
            currentLine = re.sub('//(\S)', '// \\1', line)
            currentLine = re.sub('//\s*', '// ', currentLine)
        elif "//" in line:
            currentLine = re.sub('//\s*', '// ', line)
            currentLine = re.sub('(\s*)//', '\n//', currentLine)
        else:
            currentLine = line
        outputLines.append(currentLine)
    return outputLines
    
    
def replaceIf(lines):
    def _mainFunc(line):
        return re.sub('if\s*\((.*)\)\s*\{', 'if \\1 {', line)
    def _mainStatement(line):
        return ("if" in line) and ("return" not in line)
    def _appendlineStatement(line):
        return ("{" not in line)
    return mainReplaceFunc(lines, _mainFunc, _mainStatement, _appendlineStatement)
    

class WordType(Enum):
    none = 0
    returnType = 1
    body = 2
    parameter = 3
    argument = 4
    
class RecordType(Enum):
    none = 0
    keyword = 1
    identifier = 2
    typeIdentifier = 3
    frontSpace = 4
    space = 5
    symble = 6
    text = 7
    end = 8
    
    
class WordSplit:
    word = ""
    recordList = []
    wordList = []
    wordType = WordType.none
    recordingType = RecordType.none
    
    def clear(self):
        self.word = ""
        self.recordList = []
        self.wordList = []
        self.wordType = WordType.none
        self.recordingType = RecordType.none
    
    def getWords(self):
        words = []
        for (word, type) in self.wordList:
            words.append(word)
        return words
    
    def getSearchWords(self):
        words = []
        for (word, type) in self.wordList:
            if type == WordType.body:
                words.append(self.resetWord(word))
        return words
        
    def resetWord(self, word):
        if not word.lower().find("at") == -1:
            index = word.lower().find("at")
            return word[:index+2]
        elif not word.lower().find("with") == -1:
            index = word.lower().find("with")
            return word[:index+4]
        elif not word.lower().find("from") == -1:
            index = word.lower().find("from")
            return word[:index+4]
        else:
            return word
        
    def getLine(self):
        line = ""
        for letter in self.recordList:
            line = line + letter
        return line
    
    def isSymble(self, letter):
        return letter in [")", "(", "-", ":", ";", "*"]
        
    def addCurrentWord(self, nextWordType):
        if not self.word == "":
            self.wordList.append((self.word, self.wordType))
            self.wordType = nextWordType
            self.word = ""
    
    def input(self, letter):
        # from left to right
        output = None
        if letter == " ":
            if len(self.recordList) == 0:
                self.recordList.append(letter)
                self.recordingType = RecordType.frontSpace
            else:
                if self.recordingType == RecordType.frontSpace:
                    self.recordList.append(letter)
                else:
                    if self.recordList[-1] == " ":
                        # cause last one already was space, this one can skip
                        self.recordingType = RecordType.none
                    else:
                        self.recordList.append(letter)
                        self.recordingType = RecordType.space
        elif letter == "-":
            if len(self.recordList) == 0:
                self.recordList.append(letter)
                self.recordingType = RecordType.symble
            else:
#                self.wordList.clear()
                self.recordList.clear()
                self.recordList.append(letter)
                self.recordingType = RecordType.symble
        elif letter == "(":
            if self.recordList.count("(") == 0:
                self.wordType = WordType.returnType
                if self.recordList[-1] == " ":
                    self.recordList.pop()
            else:
                self.wordType = WordType.parameter
            self.recordList.append(letter)
            self.recordingType = RecordType.symble
        elif letter == ")":
            if self.wordType == WordType.returnType:
                self.addCurrentWord(WordType.body)
            elif self.wordType == WordType.parameter:
                self.addCurrentWord(WordType.argument)
            else:
                print("error letter )")
                # todo、想定外
            if self.recordList[-1] == " ":
                self.recordList.pop()
            self.recordList.append(letter)
            self.recordingType = RecordType.symble
        elif letter == ";":
            self.addCurrentWord(WordType.none)
            if self.recordList[-1] == " ":
                self.recordList.pop()
            self.recordList.append(letter)
            self.recordingType = RecordType.end
        elif letter == "{":
            self.addCurrentWord(WordType.none)
            if not self.recordList[-1] == " ":
                self.recordList.append(" ")
            self.recordList.append(letter)
            self.recordingType = RecordType.end
        elif letter == "*":
            if not self.recordList[-1] == " ":
                self.recordList.append(" ")
            self.recordList.append(letter)
            self.recordingType = RecordType.symble
        elif letter == ":":
            self.addCurrentWord(WordType.parameter)
            if self.recordList[-1] == " ":
                self.recordList.pop()
            self.recordList.append(letter)
            self.recordingType = RecordType.text
        else:
            if self.recordList[-1] == " ":
                self.addCurrentWord(WordType.body)
                if self.isSymble(self.recordList[-2]):
                    self.recordList.pop()
            self.recordList.append(letter)
            self.recordingType = RecordType.text
            self.word = self.word + letter
                    
                    
def searchFromApple(word):
    url = 'https://developer.apple.com/search/search_data.php?q=%s' % word
    res = requests.get(url)
    return res.text
        
def replaceFunc(lines):
    def _dealStatement(currentLine):
        wordSplit = WordSplit()
        wordSplit.clear()
        for letter in currentLine:
            wordSplit.input(letter)
        line = wordSplit.getLine()
        searchWord = ""
        searchWordList = wordSplit.getSearchWords()
        if len(searchWordList) == 0:
            searchWord = ""
        elif len(searchWordList) == 1:
            searchWord = searchWordList[0]
        else:
            for word in searchWordList:
                searchWord = searchWord + word + ":"
        print(searchWord)
        if searchWord == "":
            regularExpression, replaceStr = getParaReplace(currentLine)
            currentLine = re.sub(regularExpression, replaceStr, currentLine)
        else:
            if searchWord == "tableView:cellForRowAtIndexPath:":
                result = searchFromApple(searchWord)
                for dict in result["results"]:
                
                print(result)
            
        return line
            
    def _mainFunc(currentLine):
        print("before:", currentLine)
        currentLine = _dealStatement(currentLine)
    
    #        currentLine = cleanSpace(currentLine).replace("-(", "- (").replace(") ", ")")
#        regularExpression, replaceStr = getParaReplace(currentLine)
#        currentLine = re.sub(regularExpression, replaceStr, currentLine)
        print("after :", currentLine)
        print("="*50)
        return cleanVoid(currentLine)
    def _mainStatement(line):
        return line.startswith("- (") or line.startswith("-(")
    def _appendlineStatement(line):
        return not line.endswith("{\n")
    return mainReplaceFunc(lines, _mainFunc, _mainStatement, _appendlineStatement)


def replaceExecutes(lines):
    outputLines = []
    currentLine = ""
#    appendLineFlag = False
    for i, line in enumerate(lines):
        if line.startswith("//"):
            continue
#        elif appendLineFlag:
#            if "]" not in line:
#                currentLine = currentLine + line.replace("\n", " ")
#                appendLineFlag = True
#                continue
#            else:
#                currentLine = currentLine + line
#                appendLineFlag = False
##                currentLine = re.sub("\s+", " ", currentLine)
#                regularExpression, replaceStr = getExecutesReplace(currentLine)
#                currentLine = re.sub(regularExpression, replaceStr, currentLine)
        elif ("[" in line and "@[" not in line) or (line.count("[") > line.count("@[")):
#            if "]" not in line:
#                currentLine = line.replace("\n", " ")
#                appendLineFlag = True
#                continue
#            else:
            currentLine = line
            appendLineFlag = False
#                currentLine = re.sub("\s+", " ", currentLine)
            regularExpression, replaceStr = getExecutesReplace(currentLine)
            currentLine = re.sub(regularExpression, replaceStr, currentLine)
        else:
            currentLine = line
            appendLineFlag = False
        outputLines.append(currentLine)
    return outputLines


def cleanSpace(text):
    return text.replace("  ", " ")
#    return re.sub("\s+", " ", text)


def cleanVoid(text):
    return text.replace(" -> void ", " ").replace(" -> id ", " ").replace(" :", ":").replace(" *", "").replace("*", "")


def getParaReplace(text):
    count = text.count(":")
    if count == 0:
        regularExpression = '\- \((.*)\)(.*) \{'
        replaceStr = 'func \\2() -> \\1 {'
    elif count == 1:
        regularExpression = '\- *\((.*)\)(.*):\((.*) *\**\)(.*) *\{'
        replaceStr = 'func \\2(_ \\4: \\3) -> \\1 {'
    else:
        regularExpression = '\- *\((.*)\)(.*):\((.*) *\**\)(.*)'
        replaceStr = 'func \\2(_ \\4: \\3'
        for i in range(1, count):
            paraIndex = i*3 + 1 + 1
            regularExpression = regularExpression + ' (.*):\((.*) *\**\)(.*)'
            replaceStr = replaceStr + ', \\%d \\%d: \\%d' % (paraIndex, paraIndex+2, paraIndex+1)
        regularExpression = regularExpression + ' *\{'
        replaceStr = replaceStr + ') -> \\1 {'
    return regularExpression, replaceStr


def getExecutesReplace(text):
    count = text.count(":")
    if count == 0:
        regularExpression = '\[\s*(.*) (.*)\s*\]'
        replaceStr = '\\1.\\2()'
    elif count == 1:
        regularExpression = '\[\s*(.*) (.*)\s*:\s*(.*)\s*\]'
        replaceStr = '\\1.\\2(\\3)'
    else:
#        regularExpression = ''
#        replaceStr = ''
        regularExpression = '\[\s*(.*) (.*)\s*:\s*(.*)'
        replaceStr = '\\1.\\2(\\3'
        for i in range(1, count):
            paraIndex = i*2 + 1 + 1
            regularExpression = regularExpression + ' (.*)\s*:\s*(.*)'
            replaceStr = replaceStr + ', \\%d: \\%d' % (paraIndex, paraIndex+1)
        regularExpression = regularExpression + '\s*\]'
        replaceStr = replaceStr + ')'
    return regularExpression, replaceStr
    
    
def replaceAlloc(lines):
    def _mainFunc(currentLine):
        currentLine = re.sub("\s+", " ", currentLine)
        regularExpression, replaceStr = getAllocReplace(currentLine)
        currentLine = re.sub(regularExpression, replaceStr, currentLine)
        return currentLine
    def _mainStatement(line):
        return "alloc" in line and "=" in line
    def _appendlineStatement(line):
        return "];" not in line
    return mainReplaceFunc(lines, _mainFunc, _mainStatement, _appendlineStatement)
    
    
def getAllocReplace(text):
    count = text.count(":")
    if count == 0:
        if ' *' in text:
            holder = '.* \*'
            regularExpression = '%s(.*) = \[\[(.*) alloc\]\s*init\s*\];' % holder
            replaceStr = 'let \\1 = \\2()'
        elif '* ' in text:
            holder = '.*\* '
            replaceStr = 'let \\1 = \\2()'
        else:
            holder = '\s*'
            replaceStr = '\\1 = \\2()'
        regularExpression = '%s(.*) = \[\[(.*) alloc\]\s*init\s*\];' % holder
#        print("here i go")
    elif count == 1:
        if ' *' in text:
            holder = '.* \*'
            replaceStr = 'let \\1 = \\2(\\3: \\4)'
        elif '* ' in text:
            holder = '.*\* '
            replaceStr = 'let \\1 = \\2(\\3: \\4)'
        else:
            holder = '\s*'
            replaceStr = '\\1 = \\2(\\3: \\4)'
        regularExpression = '%s(.*) = \[\[(.*) alloc\]\s*initWith(.*)\s*:\s*(.*)\];' % holder
        
    else:
        if ' *' in text:
            holder = '.* \*'
            replaceStr = 'let \\1 = \\2(\\3: \\4'
        elif '* ' in text:
            holder = '.*\* '
            replaceStr = 'let \\1 = \\2(\\3: \\4'
        else:
            holder = '\s*'
            replaceStr = '\\1 = \\2(\\3: \\4'
        regularExpression = '%s(.*) = \[\[(.*) alloc\]\s*initWith(.*)\s*:\s*(.*)' % holder
#        replaceStr = ''
#        regularExpression = '%s(.*) = \[\[(.*) alloc\]\s*initWith(.*):(.*)\];' % holder
#        replaceStr = 'let \\1 = \\2(\\3: \\4)'
        for i in range(1, count):
            paraIndex = i*2 + 3
            regularExpression = regularExpression + ' (.*):\s*(.*)'
            replaceStr = replaceStr + ', \\%d: \\%d' % (paraIndex, paraIndex + 1)
        regularExpression = regularExpression + '\s*];'
        replaceStr = replaceStr + ')'
#        print(regularExpression)
#        print(replaceStr)
    return regularExpression, replaceStr


if __name__ == '__main__':
    print("start")
    print("="*50)
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        f = open(filename)
        lines = f.readlines()
        print("open:", filename)
        print("="*50)
        outputLins = replaceComment(lines)
        outputLins = replaceFunc(outputLins)
        outputLins = replaceAlloc(outputLins)
        outputLins = replaceExecutes(outputLins)
        outputLins = replaceIf(outputLins)
        outputLins = replaceOthers(outputLins)
        f.close()
        output = ""
        for line in outputLins:
            output = output + line
#        print(output)
        print("="*50)
        print("end")
    else:
        print("need file name")
        print("="*50)
