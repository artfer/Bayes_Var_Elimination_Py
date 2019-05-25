from pandas import DataFrame
import pandas as pd
import random
import bifParser


def query(query,factors,orderBy=1,debug=False):

    query = query.replace('Pr? ','')

    #separate target variable from evidence
    q = query.split('|')

    if len(q) == 1: #no evidence
        return elimination_algorithm(factors,q,debug=debug)
    else:
        evidence = q[1].split(',') #separate evidences

        vars = [q[0]] #list of variables in query
        values = [] #list of values in evidence

        for i in range(len(evidence)):
            e = evidence[i].split("=")
            vars.append(e[0])
            values.append(e[1])
        return elimination_algorithm(factors,vars,value=values,debug=debug)


def elimination_algorithm(factors,var,value=[],orderBy=1,debug=False):

    factors = sort(factors,orderBy)

    #variables to eliminate
    elimVars = [x.name[0] for x in factors if x.name[0] not in var]
    if debug: print('variables to remove\n',elimVars,'\n')

    for variable in elimVars:

        if debug: print('eliminating',variable)

        #factors related to variable to eliminate
        joinFactors = [factor for factor in factors if variable in factor.name]
        joinFactors = sort(joinFactors,orderBy)

        if debug:
            for f in joinFactors:
                print(f.name)

        if debug:
            print('factors to join:')
            for factor in joinFactors:
                print(factor.name)
            print()

        newFactor = eliminate(variable,joinFactors,debug=False)

        #remove factors used in elimination
        factors = list(set(factors)-set(joinFactors))
        if newFactor.table['prob'].min()!=1:
            factors.append(newFactor)

    if debug:
        print('\nmostly done')
        for factor in factors:
            if debug: print(factor.table)

    #when all remaining factors contain target
    newF = lastEliminate(factors)

    if debug:
        print(newF.table)

    #if there is evidence, filter table
    if(len(var)>1):
        for i in range(1,len(var)):
            if debug: print('filter var :',var[i],'\tvalue :',value[i-1])
            newF.table = newF.table.loc[newF.table[var[i]] == value[i-1]]

        #normalize the prod column
        newF.table['prob'] = newF.table['prob'].div(newF.table['prob'].sum())

    newF.table['prob'] = newF.table['prob'].round(2)
    return newF.table['prob'].tolist()


#eliminate a single variable
def eliminate(variable,factors,debug=False):

    newF = factors[0]
    for factor in factors[1:]:

        #merge tables on variables in common
        joinOn = list(set(newF.name) & set(factor.name))
        newF.table = newF.table.merge(right=factor.table,on=joinOn)

        #get prob columns and multiply
        cols = [col for col in newF.table.columns if 'prob' in col]
        newF.table['prob'] = newF.table.loc[:, cols].prod(axis=1)
        newF.table = newF.table.drop(cols,axis=1)
        if debug: print('merged:\n',newF.table,'\n')

        #update factor name
        newF.name = newF.table.columns.tolist()
        newF.name.remove('prob')

    #group factor by variables that arent the one to eliminate
    cols = [col for col in newF.table.columns if col!='prob' and col!=variable]
    if debug: print ('group by',cols)
    newF.table = newF.table.groupby(cols,as_index=False).agg('sum')
    return newF


def lastEliminate(factors,debug=False):

    newF = factors.pop()
    for factor in factors:

        #merge tables on variables in common
        joinOn = list(set(newF.name) & set(factor.name))
        newF.table = newF.table.merge(right=factor.table,on=joinOn)

        #get prob columns and multiply
        cols = [col for col in newF.table.columns if 'prob' in col]
        newF.table['prob'] = newF.table.loc[:, cols].prod(axis=1)
        newF.table = newF.table.drop(cols,axis=1)
        if debug: print('merged:\n',newF.table,'\n')

        #update factor name
        newF.name = newF.table.columns.tolist()
        newF.name.remove('prob')

    #group factor by vars
    cols = [col for col in newF.table.columns if col!='prob']
    if debug: print ('group by',cols)
    newF.table = newF.table.groupby(cols,as_index=False).agg('sum')
    return newF

#key for sorting
def getNVars(factor):
    return len(factor.name)

#key for sorting
def getTableSize(factor):
    return factor.table.size

#returns a ordered factor list
def sort(factors,orderBy):
    if orderBy==1: #order by number of vars
        return sorted(factors,key=getNVars)

    if orderBy==2: #order by table size
        return sorted(factors,key=getTableSize)

    if orderBy==3: #random order
        random.shuffle(factors)
        return factors
