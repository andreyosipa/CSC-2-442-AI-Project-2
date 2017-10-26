import re
import random
import time

def contains(a,b):
    #function to check if list a is in list b
    a = list(a)
    b = list(b)
    result = True
    for element in a:
        result = result and (element in b)
    return result

def flat(list):
    #flat list for list of lists
    return [inner for outer in list for inner in outer]

def replace_negated(sentence):
    #remove negations from sentence with values placed
    not_replacement = {"~0" : "1", "~1" : "0"}
    for val in not_replacement.keys():
        not_parts = re.search('[\~\(\&\|\-\>]' + val + '[\)\&\|\-\<]', sentence)
        while not_parts != None:
            not_part = not_parts.group(0)[1:-1]
            sentence = simplify(sentence.replace(not_part, not_replacement[val]))
            not_parts = re.search('[\(\&\|\-\>]' + val + '[\)\&\|\-\<]', sentence)
    if ('~0' in sentence) or ('~1' in sentence):
        sentence = replace_negated(sentence)
    return sentence

def simplify(sentence):
    #function to remove some unnecessary brackets, e.g. when ((A))
    parts = re.search('\([^\~\<\>\(\)\-\&\|]*\)', sentence)
    while parts != None:
        sentence = sentence.replace(parts.group(0), parts.group(0)[1:-1])
        parts = re.search('\([^\~\<\>\(\)\-\&\|]*\)', sentence)
    return sentence

def splitted(sentence, op):
    #check if sentence is of form (P op Q), where P and Q are valid formulas and op is given operation
    if sentence[0] == '(':
        sentence = sentence[1:-1]
    counter = 0
    for idx in range(len(sentence)):
        if sentence[idx] == '(':
            counter += 1
        else:
            if sentence[idx] == ')':
                counter -= 1
            else:
                if (counter == 0) and idx + len(op) <= len(sentence):
                    flag = True
                    for op_idx in range(len(op)):
                        flag = flag and sentence[op_idx + idx] == op[op_idx]
                    if flag:
                        return [construct_sentence(sentence[:idx]), construct_sentence(sentence[idx+len(op):])]
    return None

def construct_sentence(s):
    #function to add outer brackets if needed
    brackets = 0
    minimum = len(s)
    for idx in range(0,len(s)-1):
        if s[idx] == '(':
            brackets += 1
        if s[idx] == ')':
            brackets -= 1
        minimum = min(minimum, brackets)
    if minimum == 0:
        return '(' + s + ')'
    return s

def evaluate(sentence, model):
    #function to evaluate sentence in the current model

    keys = model.keys()
    
    #put variables values
    for key in keys:
        parts = re.search('[~\(\&\|\-\>](' + key + ')[\)\&\|\-\<]', sentence)
        while (parts != None):
            part = parts.group(0)
            part = part[1:-1]
            sentence = sentence.replace(part, model[key])
            parts = re.search('[~\(\&\|\-\>](' + key + ')[\)\&\|\-\<]', sentence)
            
    sentence = simplify(sentence)
    sentence = replace_negated(sentence)
    
    #compute sentence value
    parts = re.search('(\([^\(\)]*\))', sentence)
    while parts != None:
        part = parts.group(0)
        sentence = sentence.replace(part, evaluate_simple(part))
        sentence = replace_negated(sentence)
        sentence = simplify(sentence)
        parts = re.search('(\([^\(\)]*\))', sentence)
    return bool(int(sentence))

def evaluate_clause(clause, model):
    #function to evaluate signgle disjunctive clause
    #input: clause x1|x2|x3|...|xn
    #output: True or False
    clause = construct_sentence(clause)
        
    keys = model.keys()
    
    #put variables values
    for key in keys:
        parts = re.search('[~\(\&\|\-\>](' + key + ')[\)\&\|\-\<]', clause)
        while (parts != None):
            part = parts.group(0)
            part = part[1:-1]
            clause = clause.replace(part, model[key])
            parts = re.search('[~\(\&\|\-\>](' + key + ')[\)\&\|\-\<]', clause)
            
    #as result we have string in alphabet {0,1,|}. No other symbols will be in it.
    clause = replace_negated(clause)
    
    #it is enought to have at least one True value in a clause as there is no negated values.
    if '1' in clause:
        return True
    else:
        return False

def evaluate_simple(sentence):
    #function to evaluate binary sentences like:
    #   A|B
    #   A&B
    #   A->B
    #   A<->B
    #where A,B from {0,1}

    if sentence[0] == '(' and sentence[-1] == ')':
        sentence = sentence[1:-1]
    
    #eval and = &
    if sentence == '0&0' or sentence== '0&1' or sentence == '1&0':
        return '0'
    else:
        if sentence == '1&1':
            return '1'
    
    #eval or = |
    if sentence == '1|1' or sentence== '0|1' or sentence == '1|0':
        return '1'
    else:
        if sentence == '0|0':
            return '0'
    
    #eval implication = ->
    if sentence == '0->0' or sentence== '0->1' or sentence == '1->1':
        return '1'
    else:
        if sentence == '1->0':
            return '0'
    
    #eval equivalence = <->
    if sentence == '0<->0' or sentence == '1<->1':
        return '1'
    else:
        if sentence == '1<->0' or sentence == '0<->1':
            return '0'
    
    return sentence

def evaluate_simple_test():
    #Just tests for simple clause evaluation
    val = ["0", "1"]
    operators = ['&', '|', '->', '<-', '<->']
    for op in operators:
        for v1 in val:
            for v2 in val:
                sentence = '(' + v1 + op + v2 + ')'
                res = evaluate_simple(sentence)
                print sentence + "   " + res
                sentence = v1 + op + v2
                res = evaluate_simple(sentence)
                print sentence + "   " + res

def extract_symbols(sentence):
    #function to extract all symbols from a sentence
    result = []
    #looking for everuthing that is not ()|&-<>~, but has left and right neighbors from that set 
    symbols = re.search('[\(\&\|\>\-\~][^\(\)\&\|\<\>\-\~]+[\)\&\|\<\-]', sentence)
    while (symbols != None):
        symbol = symbols.group(0)
        symbol = symbol[1:-1]
        result.append(symbol)
        #when found symbol - take it away from the sentence
        sentence = sentence.replace(symbol, '')
        symbols = re.search('[\(\&\|\>\-\~][^\(\)\&\|\<\>\-\~]+[\)\&\|\<\-]', sentence)
    return result

def tt_entails(KB, sentence):
    #input: KB is list of sentences(str)
    #       sentence is a str
    #output True or False depending on the fact that KB=>sentence or not.
    
    #find all symbols
    symbols = extract_symbols(sentence)
    for s in KB:
        symbols += extract_symbols(s)
    symbols = list(set(symbols))
    
    start = time.time()
    result = tt_check_all(KB, sentence, symbols, {})
    print "   tt_entails statistics: \n", "   elapsed time: ", round(time.time() - start,2), "s\n   # of models: ", 2**len(symbols)
    
    return result

def satisfied(KB, model):
    #function to check if KB is satisfied by the model
    #input: KB is a list of strings(sentences) or a sentence
    #       model is a dictionary
    if type(KB) == list:
        return satisfied_kb(KB, model)
    if type(KB) == str:
        return evaluate(KB, model)

def satisfied_kb(KB, model):
    #function to check if KB is satisfied by the model
    #input: KB is a list of strings(sentences)
    #       model is a dictionary

    symbols = []
    for s in KB:
        symbols += extract_symbols(s)
    symbols = set(symbols)
    
    #model must have assignments for all symbols in the KB
    if contains(symbols, set(model.keys())):
        result = True
        for s in KB:
            #evaluate sentences one by one
            result = result and evaluate(s, model)
        return result
    else:
        return False

def tt_check_all(KB, sentence, symbols, model):
    #function to check if every model of KB is a model for sentence
    #input: KB is a list of strings(sentences)
    #       sentence is a string
    #       symbols is a list of all symbols in KB and sentence that do not have an assignment in model
    #       model is a dictionary

    if len(symbols) == 0:
        if satisfied(KB, model):
            return satisfied(sentence, model)
        else:
            return True
    else:
        result = True
        model[symbols[0]] = '0'
        result = result and tt_check_all(KB, sentence, symbols[1:], model)
        model[symbols[0]] = '1'
        result = result and tt_check_all(KB, sentence, symbols[1:], model)
        return result

def cnf_to_clauses(cnf):
    #function to convert a sentence that represents cnf to a list of clauses. 
    #Sentence has all it's operators bracketed so they are unary/binary. E.g. (A|(B|C)), not (A|B|C)
    #input: cnf is string with cnf
    #note: the resulting clauses have less bracketing then it is required by convert_to_cnf as we allow A|B|C etc.
    if cnf[0] == '(':
        cnf = cnf[1:-1]
    cnf = cnf.split('&')
    result = []
    for clause in cnf:
        #remove excessive bracketing and duplicateed operators
        clause = re.sub('\(|\)', '', clause)
        clause = re.sub('(\|+)', '|', clause)
        clause = re.sub('(\~\~)+', '', clause)
        result.append('(' + clause + ')')
    return result

def convert_to_cnf(sentence):
    #function to convert sentence into cnf form
    #input: sentence is an str

    #some changes to form of sentence:
    #     replace (v) with v, where v is valiable
    #     add outer brackets if we do not have them
    parts = re.search('\([^\~\<\>\(\)\-\&\|]*\)', sentence)
    while parts != None:
        sentence = sentence.replace(parts.group(0), parts.group(0)[1:-1])
        parts = re.search('\([^\~\<\>\(\)\-\&\|]*\)', sentence)
    if sentence[0] != '(':
        sentence = '(' + sentence + ')'
    sentence = simplify(sentence)
    
    #case 1: sentence is just variable:
    parts = re.search('^\([^\~\(\)\<\-\>\&\|]*\)$', sentence)
    if parts != None:
        return sentence
    
    #case 2: sentence is (V1&V2), where Vi are variables
    parts = re.search('^\((\~?[^\(\)\<\>\-\&\|]*)\&(\~?[^\(\)\<\>\-\&\|]*)\)$', sentence)
    if parts != None:
        return '((' + parts.group(1) + ')&(' + parts.group(2) + '))'
    
    #case 3: sentence is (V1&V2), where Vi are formulas
    #parts = re.search('^\((\~?\(.*\))\&(\~?\(.*\))\)$', sentence)
    split = splitted(sentence, '&')
    if split != None:
        return '(' + construct_sentence(convert_to_cnf(split[0])) + '&' + construct_sentence(convert_to_cnf(split[1])) + ')'
    
    #case 4: sentence is (V1|V2), where Vi are variables
    parts = re.search('^\((\~?[^\(\)\<\>\-\&\|]*)\|(\~?[^\(\)\<\>\-\&\|]*)\)$', sentence)
    if parts != None:
        return sentence
    
    #case 5: sentence is (V1|V2), where Vi are formulas
    #parts = re.search('^\((\~?\(.*\))\|(\~?\(.*\))\)$', sentence)
    split = splitted(sentence, '|')
    if split != None:
        #find cnfs for both sides
        cnf_l = construct_sentence(convert_to_cnf(split[0]))
        cnf_r = construct_sentence(convert_to_cnf(split[1]))
        #splits cnf into lists of clauses
        cnf_l = cnf_to_clauses(cnf_l)
        cnf_r = cnf_to_clauses(cnf_r)
        result = '('
        for left_particle in cnf_l:
            for right_particle in cnf_r:
                result = result + '(' + construct_sentence(left_particle) + '|' + construct_sentence(right_particle) + ')&' 
        result = result[:-1]
        result += ')'
        return result
    
    #case 6: sentence is negated: (~V), where V is a varible
    parts = re.search('^\(\~[^\~\<\>\(\)\-\&\|]*\)$', sentence)
    if parts != None:
        return sentence
    
    #case 7: sentence is doubly negated: (~(~V)) or (~(~(V))) or (~~V) or (~~(V)), where V is a formula or variable
    parts = re.search('^\(\~\~(.*)\)$', sentence)
    if parts != None:
        return convert_to_cnf(parts.group(1))
    parts = re.search('^\(\~\(\~(\(.*\))\)\)$', sentence)
    if parts != None:
        return convert_to_cnf(parts.group(1))
    parts = re.search('^\(\~\(\~([^\(\)\|\&\~\<\>\-])\)\)$', sentence)
    if parts != None:
        return convert_to_cnf(parts.group(1))
    
    #case 8: sentence is of form (~(P&Q)), where P and Q are formulas or variables
    parts = re.search('^\(\~(\(.*\&.*\))\)$', sentence)
    if parts != None:
        split = splitted(parts.group(1),'&')
        if split != None:
            return convert_to_cnf('(~' + split[0] + '|~' + split[1] + ')')
    
    #case 9: sentence is of form (~(P|Q)), where P and Q are formulas or variables
    parts = re.search('^\(\~(\(.*\|.*\))\)$', sentence)
    if parts != None:
        split = splitted(parts.group(1),'|')
        if split != None:
            return convert_to_cnf('(~' + split[0] + '&~' + split[1] + ')')
        
    #case 10: sentence is of form (~(P->Q)), where P and Q are formulas or variables
    parts = re.search('^\(\~(\(.*\-\>.*\))\)$', sentence)
    if parts != None:
        split = splitted(parts.group(1),'->')
        if split != None:
            return convert_to_cnf('(' + split[0] + '&~' + split[1] + ')')
    
    #case 11: sentence is of form (~(P<->Q)), where P and Q are formulas or variables
    parts = re.search('^\(\~(\(.*\<\-\>.*\))\)$', sentence)
    if parts != None:
        split = splitted(parts.group(1),'<->')
        if split != None:
            return convert_to_cnf('((' + split[0] + '|' + split[1] + ')&(~' + split[0] + '|~' + split[1] + '))')
    
    #case 12: sentence is of form (P<->Q), where P and Q are formulas or variables
    split = splitted(sentence, '<->')
    if split != None:
        return convert_to_cnf('((' + split[0] + '->' + split[1] + ')&(' + split[1] + '->' + split[0] + '))')
    
    #case 13: sentence is of form (P->Q), where P and Q are formulas or variables
    split = splitted(sentence, '->')
    if split != None:
        return convert_to_cnf('(~' + split[0] + '|' + split[1] + ')')
    
    return sentence

def cnf(sentence):
    #function to convert sentence(str) into a list of clauses with lighter notation.
    return cnf_to_clauses(convert_to_cnf(sentence))

def satisfied_cnf(clauses, model):
    #function that checks if model satisfies list of clauses
    
    result = True
    for c in clauses:
        result = result and evaluate_clause(c,model)
    return result

def walksat(clauses, p=0.5, max_flips=1000):
    #input:
    #       clauses   : list of disjunctive clauses
    #       p         : probability of flip
    #       max_flips : max number of flips allowed
    
    start = time.time()
    
    #get symbols
    symbols = []
    for c in clauses:
        symbols += extract_symbols(c)
    symbols = list(set(symbols))
    
    #pick random model
    model = {}
    for s in symbols:
        model[s] = str(random.randint(0,1))
        
    #check if model satisfies set of clauses
    result = satisfied_cnf(clauses, model)
    
    flips = 0
    while (not result) and (flips < max_flips):
        unsatisfied = [c for c in clauses if not evaluate_clause(c,model)]
        
        #pick random unsatisfied clause
        index = random.randint(0,len(unsatisfied) - 1)
        
        c_symbols = extract_symbols(unsatisfied[index])
        
        #pick random symbol
        s_index = random.randint(0, len(c_symbols) - 1)
        
        #flip symbol with probability p
        if random.random() < p:
            if model[c_symbols[s_index]] == '1':
                model[c_symbols[s_index]] = '0'
            else:
                model[c_symbols[s_index]] = '1'
        else:
            unsatisfied_counts = []
            for s in c_symbols:
                if model[s] == '0':
                    model[s] = '1'
                else:
                    model[s] = '0'
                
                unsatisfied_counts.append(len([c for c in clauses if not evaluate_clause(c, model)]))
                
                if model[s] == '0':
                    model[s] = '1'
                else:
                    model[s] = '0'
                    
            s_index = unsatisfied_counts.index(min(unsatisfied_counts))
            s = c_symbols[s_index]
            if model[s] == '0':
                model[s] = '1'
            else:
                model[s] = '0'
                
        flips += 1
        result = satisfied_cnf(clauses,model)
    
    print "   Walksat statistics:"
    print "      elapsed time: ", round(time.time() - start,2), "s"
    print "      flips done: ", max(0,flips - 1)
    
    return result

def resolution(cnf, op_limit=10):
    #function to do resolution on a set of clauses
    #input:
    #       cnf - list of clauses
    #       op_limit - bound on number of levels to produce resolvent.
    #Note: as complexity rises fast, op_limit is small by default

    start = time.time()
    clauses = cnf
    op = 0
    while 2 and (op < op_limit):
        op += 1
        new  = []
        for c1 in clauses:
            for c2 in clauses:
                new.append(resolve(c1,c2))
        new = list(set(new))
        if ('()') in new:
            return True
        
        if set(new) <= set(clauses):
            return False
        else:
            clauses += new
            clauses = list(set(clauses))
    return False

def resolution_double(kb, alpha):
    #This function will do in parallel resolution for KB+alpha and KB+(~alpha)
    #input: kb - knowledge base as a list of sentences (not in cnf)
    #       alpha - some sentence (not in cnf)

    kb_cnf = flat([cnf(x) for x in kb])

    start = time.time()
    op_p = 0
    op_n = 0
    
    clauses_p = kb_cnf + cnf(alpha)
    clauses_n = kb_cnf + cnf(negated(alpha))
    
    continue_p = True
    continue_n = True
    while 2:
        #doing one step of resolution for first case
        if continue_p:
            op_p += 1
            new_p  = []
            for c1 in clauses_p:
                for c2 in clauses_p:
                    new_p.append(resolve(c1,c2))
            new_p = list(set(new_p))
            if ('()') in new_p:
                print "   Two-way resolution statistics:"
                print "      Result: got empty clause in KB+alpha case"
                print "      KB+alpha case:"
                print "         levels: ", op_p
                print "         current number of clauses: ", len(clauses_p)
                print "      KB+~alpha case:"
                print "         levels: ", op_n
                print "         current number of clauses: ", len(clauses_n)
                print "      elapsed time: ", round(time.time() - start, 2), "s"
                return negated(alpha)

            if set(new_p) <= set(clauses_p):
                #if resolution produces nothing new then it will be stopped
                continue_p = False
            else:
                clauses_p += new_p
                clauses_p = list(set(clauses_p))
            
        #doing one step of resolution for second case
        if continue_n:
            op_n += 1
            new_n  = []
            for c1 in clauses_n:
                for c2 in clauses_n:
                    new_n.append(resolve(c1,c2))
            new_n = list(set(new_n))
            if ('()') in new_n:
                print "   Two-way resolution statistics:"
                print "      Result: got empty clause in KB+~alpha case"
                print "      KB+alpha case:"
                print "         levels: ", op_p
                print "         current number of clauses: ", len(clauses_p)
                print "      KB+~alpha case:"
                print "         levels: ", op_n
                print "         current number of clauses: ", len(clauses_n)
                print "      elapsed time: ", round(time.time() - start, 2), "s"
                return alpha
        
            if set(new_n) <= set(clauses_n):
                #if resolution produces nothing new then it will be stopped
                continue_n = False
            else:
                clauses_n += new_n
                clauses_n = list(set(clauses_n))
        
        if not (continue_p or continue_n):
            print "   Two-way resolution statistics:"
            print "      Result: not able to get empty clause in any of the cases"
            print "      KB+alpha case:"
            print "         levels: ", op_p
            print "         current number of clauses: ", len(clauses_p)
            print "      KB+~alpha case:"
            print "         levels: ", op_n
            print "         current number of clauses: ", len(clauses_n)
            print "      elapsed time: ", round(time.time() - start, 2), "s"
            return False

def resolve(clause1, clause2):
    #function to resolve two clauses
    #input: clause# - str that represents a clause

    if clause1[0] == '(':
        clause1 = clause1[1:-1]
    if clause2[0] == '(':
        clause2 = clause2[1:-1]
    
    #check if there is the only pair to resolve
    if len([x for x in clause1.split('|') if negated(x) in clause2.split('|')]) != 1:
        return '(' + clause1 + ')'
    
    #find all terms for resolvent
    resolvent = [x for x in clause1.split('|') if not negated(x) in clause2.split('|')] + [x for x in clause2.split('|') if not negated(x) in clause1.split('|')]
    
    #remove duplicates in resolvent and sort it to reduce amount of them in the future
    resolvent = sorted(list(set(resolvent)))
    if len(resolvent) == 0:
        return '()'
    answer = '('
    for r in resolvent:
        answer = answer + r + '|'
    answer = answer[:-1] + ')'
    return answer

def negated(x):
    #function to return negated statement
    if x[0] == '~':
        return x[1:]
    else:
        return '~'+x

def examples_entailment():
    #function to run examples using entailment

    print "\n\n\n\n\nEXAMPLES WITH ENTAILMENT ALGORITHM"

    #1.Modus Ponens
    print "1.Modus Ponens:"
    KB = ['(P)', '(P->Q)']
    alpha = '(Q)'
    if tt_entails(KB, alpha):
        print KB, 'entails ', alpha
    else:
        print KB, 'does not entail ', alpha
        
    #2.Wumpus World
    print "\n\n2.Wumpus World:"
    KB = ['(~P11)', '(B11<->(P12|P21))', '(B21<->((P11|P22)|P31))', '(~B11)', '(B21)']
    alpha = '(P12)'
    if tt_entails(KB, alpha):
        print alpha, " is true"
    else:
        print '~'+alpha, " is true"
        
    #3.Horn Clauses:
    print "\n\n3.Horn Clauses:"
    KB = ['(Mythical->Immortal)', '(~Mythical->~Immortal)', '((Immortal|Mammal)->Horned)', '(Horned->Magical)']
    alpha = ['(Mythical)', '(Magical)', '(Horned)']
    for a in alpha:
        if  (not tt_entails(KB, a)) and (not tt_entails(KB, '(~' + a[1:])) :
            print "we can not prove anything about ", a
        
    #4.Liars and Truth-tellers (a)
    #Each name variable X here means that "X is truth-teller"
    print "\n\n4.Liars and truth-tellers (a)"
    KB = ['(Amy<->(Cal&Amy))', '(Bob<->~Cal)', '(Cal<->(Bob|~Amy))']
    alphas = ['(Amy)', '(Bob)', '(Cal)']
    for a in alphas:
        if tt_entails(KB, a):
            print a, "is truth-teller"
        if tt_entails(KB, '(~' + a[1:]):
            print a, "is liar"
        
    #4.Liars and Truth-tellers (b)
    #Each name variable X here means that "X is truth-teller"
    #Here assuming that "Bob is correct" means "What Bob said is truth", which is equivalent to what Bob said
    print "\n\n4.Liars and truth-tellers (b)"
    KB = ['(Amy<->(~Cal))', '(Bob<->(Amy&Cal))', '(Cal<->(Amy&Cal))']
    alpha = ['(Amy)', '(Bob)', '(Cal)']
    for a in alpha:
        if tt_entails(KB,a):
            print a[1:-1], "is truth-teller"
        if tt_entails(KB, '(~'+a[1:]):
            print a[1:-1], "is liar"
        
    #5.More Liars and Truth-tellers
    #symbols definitions as in previous case
    print "\n\n5.More Liars and truth-tellers"
    KB = ['(Amy<->(Hal&Ida))', 
          '(Bob<->(Amy&Lee))', 
          '(Cal<->(Bob&Gil))', 
          '(Dee<->(Eli&Lee))', 
          '(Eli<->(Cal&Hal))', 
          '(Fay<->(Dee&Ida))', 
          '(Gil<->(~Eli&~Jay))', 
          '(Hal<->(~Fay&~Kay))', 
          '(Ida<->(~Gil&~Kay))', 
          '(Jay<->(~Amy&~Cal))', 
          '(Kay<->(~Dee&~Fay))', 
          '(Lee<->(~Bob&~Jay))']
    alpha = ['(Amy)', '(Bob)', '(Cal)', '(Dee)', '(Eli)', '(Fay)', '(Gil)', '(Hal)', '(Ida)', '(Jay)', '(Kay)', '(Lee)']
    for a in alpha:
        if tt_entails(KB,a):
            print a[1:-1], "is truth-teller"
        if tt_entails(KB, '(~'+a[1:]):
            print a[1:-1], "is liar"
            
    #6.The Doors of Enlightenment (a) 
    #For each x in A, B, C, D, E, F, G, and H we assume x means "x is a knight" and ~x means "x is a knave"
    #For each x in X Y Z we assume x means "x is a good door" and ~x means "x is a bad door"
    #Assume "Either x or y" is exclusive or (despite it is not like that in real life)
    print"\n\n6.The Doors of Enlightenment (a)"
    KB = ['(A<->X)', 
          '(B<->(Y|Z))', 
          '(C<->(A&B))', 
          '(D<->(X&Y))', 
          '(E<->(X&Z))', 
          '(F<->((D&~E)|(~D&E)))',
          '(G<->(C->F))', 
          '(H<->((G&H)->A))']
    alphas = ['(X)', '(Y)', '(Z)']
    for a in alphas:
        if tt_entails(KB,a):
            print "Philosopher can choose door", a[1:-1]
            #"can" here is in case solution is not unique
            
    #6.The Doors of Enlightenment (b) 
    #For each x in A, B, C, D, E, F, G, and H we assume x means "x is a knight" and ~x means "x is a knave"
    #For each x in X Y Z we assume x means "x is a good door" and ~x means "x is a bad door"
    #Assume "Either x or y" is exclusive or (despite it is not like that in real life)
    print"\n\n6.The Doors of Enlightenment (b)"
    KB = ['(A<->X)', 
          '(H<->((G&H)->A))',
          '(C<->(A&((((((B|C)|D)|E)|F)|G)|H)))',
          '(~G->C)']
    #Reasoning for last fact:
    # G: If C is a knight ...
    # If G is a liar then we do not have any information about C as it can take any, depending on ...
    # But if G is a knave, then C->(...) is False which only happens when C=True and (...)=True.
    # As we do not know anything about ..., then G=False means C=True for us.
    alphas = ['(X)', '(Y)', '(Z)']
    for a in alphas:
        if tt_entails(KB,a):
            print "Philosopher can choose door", a[1:-1]
            #"can" here is in case solution is not unique

def examples_walksat():
    #function to run examples using walksat algorithm

    #Here the *proofs* are of the following scheme: we take KB + ~goal and check if we achieve nothing from walksat. 
    #This result we interpret as proof of unsatisfiability, despite this is completely illegal in math terms.
    
    print "\n\n\n\n\nEXAMPLES WITH WALKSAT ALGORITHM"

    #1.Modus Ponens
    #This problem can not be proved, so the correct way to interpret the result is "it seems to be True/False".
    print "1.Modus Ponens:"
    KB = ['(P)', '(P->Q)']
    alpha = '(Q)'
    not_alpha = construct_sentence(negated(alpha))
    KB_cnf_1 = flat([cnf(x) for x in KB] + [cnf(alpha)])
    KB_cnf_2 = flat([cnf(x) for x in KB] + [cnf(not_alpha)])
    if walksat(KB_cnf_1) and not walksat(KB_cnf_2):
        print KB, 'seems to entail ', alpha
        
    #2.Wumpus World
    print "\n\n2.Wumpus World:"
    KB = ['(~P11)', '(B11<->(P12|P21))', '(B21<->((P11|P22)|P31))', '(~B11)', '(B21)']
    alpha = '(P12)'
    not_alpha = construct_sentence(negated(alpha))
    KB_cnf_1 = flat([cnf(x) for x in KB] + [cnf(not_alpha)])
    KB_cnf_2 = flat([cnf(x) for x in KB] + [cnf(alpha)])
    if walksat(KB_cnf_1) and not walksat(KB_cnf_2):
        print alpha, " seems to be false"
    else:
        if not walksat(KB_cnf_1) and walksat(KB_cnf_2):
            print alpha, " seems to be true"
        
    #3.Horn Clauses:
    print "\n\n3.Horn Clauses:"
    KB = ['(Mythical->Immortal)', '(~Mythical->~Immortal)', '((Immortal|Mammal)->Horned)', '(Horned->Magical)']
    alphas = ['(Mythical)', '(Magical)', '(Horned)']
    for a in alphas:
        KB_cnf_1 = flat([cnf(x) for x in KB] + [cnf(a)])
        KB_cnf_2 = flat([cnf(x) for x in KB] + [cnf(negated(a))])
        if (walksat(KB_cnf_1) and walksat(KB_cnf_2)):
            print "we can not prove anything about ", a
    
    #4.Liars and Truth-tellers (a)
    #Each name variable X here means that "X is truth-teller"
    print "\n\n4.Liars and truth-tellers (a)"
    KB = ['(Amy<->(Cal&Amy))', '(Bob<->~Cal)', '(Cal<->(Bob|~Amy))']
    alpha = ['(Amy)', '(Bob)', '(Cal)']
    for a in alpha:
        KB_cnf = flat([cnf(x) for x in KB] + [cnf(a)])
        if walksat(KB_cnf):
            print a, " is a truth-teller"
        else:
            print a, " seems to be a liar"
            
    #4.Liars and Truth-tellers (b)
    #Each name variable X here means that "X is truth-teller"
    #Here assuming that "Bob is correct" means "What Bob said is truth", which is equivalent to what Bob said
    print "\n\n4.Liars and truth-tellers (b)"
    KB = ['(Amy<->(~Cal))', '(Bob<->(Amy&Cal))', '(Cal<->(Amy&Cal))']
    alpha = ['(Amy)', '(Bob)', '(Cal)']
    for a in alpha:
        KB_cnf = flat([cnf(x) for x in KB] + [cnf(a)])
        if walksat(KB_cnf):
            print a, " is a truth-teller"
        else:
            print a, " seems to be a liar"
                      
    #5.More Liars and Truth-tellers
    #symbols definitions as in previous case
    print "\n\n5.More Liars and truth-tellers"
    KB = ['(Amy<->(Hal&Ida))', 
          '(Bob<->(Amy&Lee))', 
          '(Cal<->(Bob&Gil))', 
          '(Dee<->(Eli&Lee))', 
          '(Eli<->(Cal&Hal))', 
          '(Fay<->(Dee&Ida))', 
          '(Gil<->(~Eli&~Jay))', 
          '(Hal<->(~Fay&~Kay))', 
          '(Ida<->(~Gil&~Kay))', 
          '(Jay<->(~Amy&~Cal))', 
          '(Kay<->(~Dee&~Fay))', 
          '(Lee<->(~Bob&~Jay))']
    alpha = ['(Amy)', '(Bob)', '(Cal)', '(Dee)', '(Eli)', '(Fay)', '(Gil)', '(Hal)', '(Ida)', '(Jay)', '(Kay)', '(Lee)']
    for a in alpha:
        KB_cnf = flat([cnf(x) for x in KB] + [cnf(a)])
        if walksat(KB_cnf):
            print a, " is a truth-teller"
        else:
            print a, " seems to be liar"
            
    #6.The Doors of Enlightenment (a) 
    #For each x in A, B, C, D, E, F, G, and H we assume x means "x is a knight" and ~x means "x is a knave"
    #For each x in X Y Z we assume x means "x is a good door" and ~x means "x is a bad door"
    #Assume "Either x or y" is exclusive or (despite it is not like that in real life)
    print"\n\n6.The Doors of Enlightenment (a)"
    KB = ['(A<->X)', 
          '(B<->(Y|Z))', 
          '(C<->(A&B))', 
          '(D<->(X&Y))', 
          '(E<->(X&Z))', 
          '(F<->((D&~E)|(~D&E)))',
          '(G<->(C->F))', 
          '(H<->((G&H)->A))']
    alphas = ['(X)', '(Y)', '(Z)']
    for a in alphas:
        KB_cnf_1 = flat([cnf(x) for x in KB] + [cnf(a)])
        KB_cnf_2 = flat([cnf(x) for x in KB] + [cnf(negated(a))])
        if walksat(KB_cnf_1) and not walksat(KB_cnf_2):
            print "Philosopher can choose door", a, "as it seems to be good"
            
    #6.The Doors of Enlightenment (b) 
    #For each x in A, B, C, D, E, F, G, and H we assume x means "x is a knight" and ~x means "x is a knave"
    #For each x in X Y Z we assume x means "x is a good door" and ~x means "x is a bad door"
    #Assume "Either x or y" is exclusive or (despite it is not like that in real life)
    print"\n\n6.The Doors of Enlightenment (b)"
    KB = ['(A<->X)', 
          '(H<->((G&H)->A))',
          '(C<->(A&((((((B|C)|D)|E)|F)|G)|H)))',
          '(~G->C)']
    #Reasoning for last fact:
    # G: If C is a knight ...
    # If G is a liar then we do not have any information about C as it can take any, depending on ...
    # But if G is a knave, then C->(...) is False which only happens when C=True and (...)=True.
    # As we do not know anything about ..., then G=False means C=True for us.
    alphas = ['(X)', '(Y)', '(Z)']
    for a in alphas:
        KB_cnf_1 = flat([cnf(x) for x in KB] + [cnf(a)])
        KB_cnf_2 = flat([cnf(x) for x in KB] + [cnf(negated(a))])
        if walksat(KB_cnf_1) and not walksat(KB_cnf_2):
            print "Philosopher can choose door", a, "as it seems to be good"

def examples_resolution():
    #function to run examples using resolution algorithm

    print "\n\n\n\n\nEXAMPLES WITH RESOLUTION ALGORITHM"

    #1.Modus Ponens
    print "1.Modus Ponens:"
    KB = ['(P)', '(P->Q)']
    alpha = '(Q)'
    not_alpha = construct_sentence(negated(alpha))
    KB_cnf = [cnf(x) for x in KB] + [cnf(not_alpha)]
    KB_cnf = flat(KB_cnf)
    if resolution(KB_cnf):
        print KB, 'entails ', alpha
    else:
        print KB, 'does not entail ', alpha
        
    #2.Wumpus World
    print "\n\n2.Wumpus World:"
    KB = ['(~P11)', '(B11<->(P12|P21))', '(B21<->((P11|P22)|P31))', '(~B11)', '(B21)']
    alpha = '(P12)'
    print resolution_double(KB, alpha), "is true"
        
    #4.Liars and Truth-tellers (a)
    #Each name variable X here means that "X is truth-teller"
    print "\n\n4.Liars and truth-tellers (a)"
    KB = ['(Amy<->(Cal&Amy))', '(Bob<->~Cal)', '(Cal<->(Bob|~Amy))']
    alpha = ['(Amy)', '(Bob)', '(Cal)']
    for a in alpha:
        if resolution_double(KB, a) == a:
            print a, "is truth-teller"
        else:
            print a, "is liar"
            
    #4.Liars and Truth-tellers (b)
    #Each name variable X here means that "X is truth-teller"
    #Here assuming that "Bob is correct" means "What Bob said is truth", which is equivalent to what Bob said
    print "\n\n4.Liars and truth-tellers (b)"
    KB = ['(Amy<->(~Cal))', '(Bob<->(Amy&Cal))', '(Cal<->(Amy&Cal))']
    alpha = ['(Amy)', '(Bob)', '(Cal)']
    for a in alpha:
        result = resolution_double(KB, a)
        if result == a:
            print a, "is truth-teller"
        if result == negated(a):
            print a, "is liar"

examples_entailment()
examples_walksat()
examples_resolution()