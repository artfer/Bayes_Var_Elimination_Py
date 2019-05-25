from pandas import DataFrame
import re


class Node:
    def __init__(self,name,parents,children,table):
        self.name = name
        self.parents = parents
        self.children = children
        self.table = table

class Factor:
    def __init__(self,name,table):
        self.name=name
        self.table=table


def getFactors(nodes,debug=False):
    factors = []
    for node in nodes:
        name = [node.name] + [x.name for x in node.parents]
        if debug: print (name)
        factors.append(Factor(name,node.table))
        if debug: print (node.table)
    return factors


def parser(file):
    infile = open(file)
    #print (infile)

    # Regex patterns for parsing
    variable_pattern = re.compile(r"  type discrete \[ \d+ \] \{ (.+) \};\s*")
    prior_probability_pattern_1 = re.compile(
        r"probability \( ([^|]+) \) \{\s*")
    prior_probability_pattern_2 = re.compile(r"  table (.+);\s*")
    conditional_probability_pattern_1 = (
        re.compile(r"probability \( (.+) \| (.+) \) \{\s*"))
    conditional_probability_pattern_2 = re.compile(r"  \((.+)\) (.+);\s*")

    variables = {}  # domains
    functions = []  # function names (nodes/variables)

    nodes = []
    # For every line in the file

    while True:
        line = infile.readline()

        # End of file
        if not line:
            break

        # Variable declaration
        if line.startswith("variable"):
            match = variable_pattern.match(infile.readline())
            # Extract domain and place into dictionary
            if match:
                variables[line[9:-3]] = match.group(1).split(", ")
                #print (variables)


        # Probability distribution
        elif line.startswith("probability"):

            match = prior_probability_pattern_1.match(line)
            if match:

                # Prior probabilities
                variable = match.group(1)
                #print (variable)
                function_name = variable
                functions.append(function_name)
                line = infile.readline()
                match = prior_probability_pattern_2.match(line)
                dictionary = dict(zip(variables[variable],map(float, match.group(1).split(", "))))


                rows = []
                for row in dictionary:
                    rows.append([row,dictionary[row]])
                table = DataFrame(rows,columns=[variable,'prob'])
                nodes.append(Node(variable,[],[],table))


            else:
                match = conditional_probability_pattern_1.match(line)
                if match:

                    # Conditional probabilities
                    variable = match.group(1)
                    #print ("1",variable)

                    function_name = variable
                    functions.append(function_name)
                    given = match.group(2).split(", ")


                    allCols = [x for x in given]
                    allCols.append(variable)
                    allCols.append('prob')

                    #print (given)
                    dictionary = {}

                while True:
                        line = infile.readline()  # line of the CPT
                        if line == '}\n':
                            break
                        match = conditional_probability_pattern_2.match(line)
                        given_values = match.group(1).split(", ")
                        for value, prob in zip(
                                variables[variable],
                                map(float, match.group(2).split(", "))):
                            dictionary[tuple(given_values + [value])] = prob
                        #print (dictionary)

                rows = []
                for row in dictionary:
                    x = []
                    for var in row:
                        x.append(var)
                    x.append(dictionary[row])
                    rows.append(x)
                #print (rows)

                table = DataFrame(rows,columns=allCols)


                tmp = Node(variable,[],[],table)

                for node in nodes:
                        if node.name in given:
                            node.children.append(tmp)
                            tmp.parents.append(node)

                nodes.append(tmp)
    return nodes
