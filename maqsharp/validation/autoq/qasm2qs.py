"""Translates the repeat-until-success benchmarks of AutoQ 2.0 (OpenQASM 3) into Q#.

    python3 qasm2qs.py <AutoQ>/benchmarks/TACAS25/RUS > rus.qs
"""
import re, sys, os
G = {'h':'H','t':'T','tdg':'Adjoint T','s':'S','sdg':'Adjoint S','x':'X','z':'Z','y':'Y','cz':'CZ','cx':'CNOT'}
def stmts(lines):
    out=[]
    for l in lines:
        l=l.split('//')[0].strip()
        m=re.match(r'(\w+)\s+qb\[(\d)\](?:,\s*qb\[(\d)\])?;',l)
        if m:
            g,a,b=m.groups(); q=lambda i: ['anc','t'][int(i)]
            out.append(f"{G[g]}({q(a)}{', '+q(b) if b else ''});")
    return out
def conv(name, path):
    src=open(path).read()
    pre, rest = src.split('outcome[0] = measure qb[0];',1)
    body = rest.split('while (!outcome[0]) {',1)[1].rsplit('}',1)[0]
    body = body.replace('outcome[0] = measure qb[0];','')
    p=stmts(pre.splitlines()); b=stmts(body.splitlines())
    ind='        '
    return (f"    operation {name}(anc : Qubit, t : Qubit) : Unit {{\n"
            + ''.join(ind+s+'\n' for s in p)
            + f"{ind}mutable r = M(anc);\n{ind}while r == Zero {{\n"
            + ''.join(ind+'    '+s+'\n' for s in b)
            + f"{ind}    set r = M(anc);\n{ind}}}\n{ind}Reset(anc);\n    }}\n")
root=sys.argv[1]
names=['Figure7','Figure8','Figure9','Figure10a','Figure10b','Figure10c']
print("namespace AutoQRUS {\n    // repeat-until-success programs of the AutoQ 2.0 benchmarks (TACAS 2025),\n    // translated gate by gate; qb[0] is anc and qb[1] is t\n")
for n in names: print(conv(n, os.path.join(root,n,'circuit.qasm')))
print("}")
