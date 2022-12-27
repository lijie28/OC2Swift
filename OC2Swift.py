import sys
import re

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
    

def replaceFunc(lines):
    def _mainFunc(currentLine):
        currentLine = cleanSpace(currentLine).replace("-(", "- (").replace(") ", ")")
        regularExpression, replaceStr = getParaReplace(currentLine)
        currentLine = re.sub(regularExpression, replaceStr, currentLine)
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
        print(output)
        print("="*50)
        print("end")
    else:
        print("need file name")
        print("="*50)
