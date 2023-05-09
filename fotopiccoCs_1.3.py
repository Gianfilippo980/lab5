#Programma per l'analisi degli spettri
#Fit con due gaussiane e un'esponenziale

import ROOT
import os
from array import array


def Elenco (path):
    dir=os.listdir(path)
    spettri=[]
    for f in dir:
            if f.endswith(".mca"):
                spettri.append(f)
    return spettri

def Lettura (path, nome):
    file=open(nome,errors='ignore')
    righe=file.readlines()
    file.close()
    #print(righe)
    return righe

def Spettro (path, nome):
    righe=Lettura(path, nome)
    inizio=righe.index("<<DATA>>\n") + 1
    fine=righe.index("<<END>>\n")
    scala=1
    if "GAIA=2;    Analog Gain Index\n" in righe:
        scala=10
    #vogliamo riconoscere gli spettri cono sfondoscala 10 V
    return righe[inizio:fine], scala

def Estremi (path, nome):
    estremo_sp=[0,8192]
    estremi_g1=[2000,4000]
    #valori di default, restiuiti se non esiste un valore nel .txt
    esiste=os.path.isfile(path+"/Estremi_1g.txt")
    if not esiste :
        intesta="Nome, min-gaus, max-gaus, min-spettro, max-spettro\n"
        Scrivi (path, "Estremi_1g.txt", intesta)    
    righe=Lettura(path, "Estremi_1g.txt")
    trovato=False
    for r in righe:
        if r.startswith(nome):
            r=r.split(", ")
            estremi_g1=[int(r[1]), int(r[2])]
            estremo_sp=[int(r[3]), int(r[4])]
            trovato=True
            break
    if not trovato:
        default=str(estremi_g1[0])+", "+str(estremi_g1[1])+", "+str(estremo_sp[0])+", "+str(estremo_sp[1])
        Scrivi (path, "Estremi_1g.txt", nome+", "+default+"\n")
    return estremo_sp, estremi_g1

def Scrivi (path, nome, valori):
    #Scrive "valori" sul file "nome" nel "path"
    file=open(nome, "a")
    file.write(valori)
    file.close
    return

def Salva (path, nome, parametri, scala, chi_2):
    log=nome+"    "
    for p in parametri:
        log=log+str(p)+"    "
    log=log+str(scala) + "    " + str(chi_2)+"\n"
    Scrivi(path, "fit_1g.txt", log)
    return

h=[]
c=[]
intesta="Nome Costante Errore Media Errore Sigma Errore Scala Chi2 Voltaggio\n"
file=open("fit_1g.txt", 'w')
file.write(intesta)
file.close()
#questa operazione cancelal il contenuto precedente del file con i risultati
risultati=array( 'd', 6*[0.] )
path=os.getcwd()
files=Elenco(path)
for j in range(len(files)):
    f=files[j]
    print ("Trattando: ", f)
    estremi_spettro, estremi_g1= Estremi(path, f)
    c.append(ROOT.TCanvas())
    h.append(ROOT.TH1F(f, f, 8192, 0 ,8192))
    gauss1=ROOT.TF1("gauss1", "gaus", estremi_g1[0], estremi_g1[1])    
    spettro, fondoscala=Spettro(path, f)
    for i in range(len (spettro)):
        h[j].SetBinContent(i+1, int(spettro[i]))    
    h[j].Fit(gauss1, "R+", "")
    parametri_g1=gauss1.GetParameters()
    errori_g1=gauss1.GetParErrors()
    for k in range(3):
        risultati[k*2]=parametri_g1[k]
        risultati[k*2+1]=errori_g1[k]
    chi_2=gauss1.GetChisquare()
    Salva (path, f, risultati, fondoscala, chi_2)
    h[j].GetXaxis().SetRange(estremi_spettro[0], estremi_spettro[1])
    c[j].Draw()
    c[j].SaveAs(f.replace('.mca', '.pdf'))
Scrivi(path, "fit_1g.txt", "\n")
input ("Premere un tasto per terminare")