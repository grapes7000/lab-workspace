from dataclasses import dataclass,field
from typing import Optional
import re

ATOMIC_WEIGHTS={
"H":1.008,"He":4.0026,"Li":6.94,"Be":9.0122,"B":10.81,"C":12.011,"N":14.007,"O":15.999,"F":18.998,"Ne":20.180,
"Na":22.990,"Mg":24.305,"Al":26.982,"Si":28.085,"P":30.974,"S":32.06,"Cl":35.45,"Ar":39.948,"K":39.098,"Ca":40.078,
"Sc":44.956,"Ti":47.867,"V":50.942,"Cr":51.996,"Mn":54.938,"Fe":55.845,"Co":58.933,"Ni":58.693,"Cu":63.546,"Zn":65.38,
"Ga":69.723,"Ge":72.630,"As":74.922,"Se":78.971,"Br":79.904,"Kr":83.798,"Rb":85.468,"Sr":87.62,"Y":88.906,"Zr":91.224,
"Nb":92.906,"Mo":95.95,"Ru":101.07,"Rh":102.91,"Pd":106.42,"Ag":107.87,"Cd":112.41,"In":114.82,"Sn":118.71,"Sb":121.76,
"Te":127.60,"I":126.90,"Xe":131.29,"Cs":132.91,"Ba":137.33,"La":138.91,"Ce":140.12,"Pr":140.91,"Nd":144.24,"Sm":150.36,
"Eu":151.96,"Gd":157.25,"Tb":158.93,"Dy":162.50,"Ho":164.93,"Er":167.26,"Tm":168.93,"Yb":173.05,"Lu":174.97,"Hf":178.49,
"Ta":180.95,"W":183.84,"Re":186.21,"Os":190.23,"Ir":192.22,"Pt":195.08,"Au":196.97,"Hg":200.59,"Tl":204.38,"Pb":207.2,"Bi":208.98,
"Th":232.04,"Pa":231.04,"U":238.03}
TOKEN=re.compile(r"[A-Z][a-z]?|\d+(?:\.\d+)?|[()\[\]]")

def parse_formula(formula):
 text=formula.strip().replace(" ","")
 if not text: raise ValueError("Formula is required")
 tokens=TOKEN.findall(text)
 if ''.join(tokens)!=text: raise ValueError("Unsupported formula notation")
 stack=[{}]; brackets=[]; i=0
 while i<len(tokens):
  token=tokens[i]
  if token in ('(','['): stack.append({}); brackets.append(token); i+=1
  elif token in (')',']'):
   if len(stack)==1: raise ValueError("Unmatched closing bracket")
   opening=brackets.pop()
   if (opening,token) not in (("(",")"),("[","]")): raise ValueError("Mismatched brackets")
   group=stack.pop(); i+=1; mult=1.0
   if i<len(tokens) and tokens[i][0].isdigit(): mult=float(tokens[i]); i+=1
   for element,count in group.items(): stack[-1][element]=stack[-1].get(element,0)+count*mult
  elif token[0].isupper():
   if token not in ATOMIC_WEIGHTS: raise ValueError(f"Unknown element: {token}")
   i+=1; count=1.0
   if i<len(tokens) and tokens[i][0].isdigit(): count=float(tokens[i]); i+=1
   stack[-1][token]=stack[-1].get(token,0)+count
  else: raise ValueError("Unexpected multiplier")
 if len(stack)!=1: raise ValueError("Unclosed bracket")
 return stack[0]

def molar_mass(formula): return sum(ATOMIC_WEIGHTS[e]*n for e,n in parse_formula(formula).items())
MASS={"kg":1000,"g":1,"mg":.001,"ug":1e-6}
VOL={"L":1,"mL":.001,"uL":1e-6}
AMOUNT={"mol":1,"mmol":.001,"umol":1e-6}
DENSITY={"g/L":1,"g/mL":1000,"kg/L":1000,"mg/mL":1}

def convert(value,unit,kind):
 maps={"mass":MASS,"volume":VOL,"amount":AMOUNT,"density":DENSITY}
 if unit not in maps[kind]: raise ValueError(f"Unsupported {kind} unit: {unit}")
 return float(value)*maps[kind][unit]

@dataclass
class Species:
 side:str; name:str=""; formula:str=""; coefficient:float=1; mw:Optional[float]=None
 mass:Optional[float]=None; mass_unit:str="g"; volume:Optional[float]=None; volume_unit:str="mL"
 density:Optional[float]=None; density_unit:str="g/mL"; moles:Optional[float]=None; amount_unit:str="mol"
 purity:float=100; actual_yield:Optional[float]=None; warnings:list[str]=field(default_factory=list)

@dataclass
class ReactionResult:
 balanced:bool; limiting:str|None; extent:float|None; rows:list[dict]; steps:list[str]; warnings:list[str]

def derive(s):
 mw=s.mw or (molar_mass(s.formula) if s.formula else None)
 mass=convert(s.mass,s.mass_unit,"mass") if s.mass is not None else None
 volume=convert(s.volume,s.volume_unit,"volume") if s.volume is not None else None
 density=convert(s.density,s.density_unit,"density") if s.density is not None else None
 moles=convert(s.moles,s.amount_unit,"amount") if s.moles is not None else None
 purity=s.purity/100
 if mass is None and volume is not None and density is not None: mass=volume*density
 if volume is None and mass is not None and density not in (None,0): volume=mass/density
 if density is None and mass is not None and volume not in (None,0): density=mass/volume
 if moles is None and mass is not None and mw not in (None,0): moles=mass*purity/mw
 if mass is None and moles is not None and mw is not None and purity>0: mass=moles*mw/purity
 return {"mw":mw,"mass_g":mass,"volume_L":volume,"density_g_L":density,"moles":moles}

def check_balance(species):
 left={}; right={}
 for s in species:
  if not s.formula:return False,{},{}
  target=left if s.side=="reactant" else right
  for e,n in parse_formula(s.formula).items():target[e]=target.get(e,0)+n*s.coefficient
 return all(abs(left.get(e,0)-right.get(e,0))<1e-9 for e in set(left)|set(right)),left,right

def calculate_reaction(species):
 if not species or not any(s.side=="reactant" for s in species) or not any(s.side=="product" for s in species):raise ValueError("Add at least one reactant and product")
 if any(s.coefficient<=0 for s in species):raise ValueError("Coefficients must be positive")
 balanced,left,right=check_balance(species)
 derived=[derive(s) for s in species]; warnings=[]; steps=[]
 if not balanced:warnings.append(f"Reaction is unbalanced. Reactants {left}; products {right}")
 candidates=[]
 for s,d in zip(species,derived):
  if s.side=="reactant" and d["moles"] is not None:candidates.append((d["moles"]/s.coefficient,s.name or s.formula))
 extent=min((x[0] for x in candidates),default=None); limiting=min(candidates)[1] if candidates else None
 if extent is not None:steps.append("Reaction extent is the minimum of available moles / coefficient.")
 rows=[]
 for s,d in zip(species,derived):
  theoretical=extent*s.coefficient if extent is not None else None
  remaining=(d["moles"]-theoretical) if s.side=="reactant" and theoretical is not None and d["moles"] is not None else None
  theoretical_mass=theoretical*d["mw"] if theoretical is not None and d["mw"] is not None else None
  percent=None
  if s.side=="product" and s.actual_yield is not None and theoretical_mass not in (None,0):
   percent=s.actual_yield/theoretical_mass*100
   if percent>100:warnings.append(f"{s.name or s.formula}: actual yield exceeds theoretical yield")
  rows.append({**d,"name":s.name,"formula":s.formula,"side":s.side,"coefficient":s.coefficient,"theoretical_moles":theoretical,"remaining_moles":remaining,"theoretical_mass_g":theoretical_mass,"percent_yield":percent})
 return ReactionResult(balanced,limiting,extent,rows,steps,warnings)
