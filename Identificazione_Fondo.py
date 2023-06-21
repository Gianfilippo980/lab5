import ROOT
from array import array
from time import sleep

"""Questioni Stilistiche"""
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptFit(1)

class Istogramma:
    """Incapsulatore per l'istogramma di Root"""
    intercetta = 7.71
    c_angolare = 2.938

    def __init__ (self, file_dati, file_fondo=False):
        """L'argomento file_fondo è optional, se non specificato, il fondo può essere sottratto con
        una successuva operazione"""
        self.canvas=ROOT.TCanvas()
        file=open(file_dati, errors='ignore')
        righe=file.readlines()
        file.close()
        inizio=righe.index("<<DATA>>\n") + 1
        fine=righe.index("<<END>>\n")
        self.n_chan = fine-inizio
        self.isto=ROOT.TH1F(file_dati, file_dati, self.n_chan, 0, (self.n_chan- self.intercetta)/self.c_angolare)
        """questi sono gli indici del primo bin e dell'ultimo"""
        if "GAIA=2;    Analog Gain Index\n" in righe:
            self.scala=10
            """Questo è il fondoscala in V dello spettro"""
        else:
            self.scala=1
        self.spettro=list(map(int, righe[inizio:fine]))
        if file_fondo:
            self.__SottraiFondo(file_fondo)
        self.__AggiornaIsto()

    def SottraiFondo(self, file_fondo):
        """Utilizzare questo metodo se non si è sottratto il fondo nel momento in cui si è instanziato l'istogramma,
        o se si si desidera sottrarre un ulteriore spettro"""
        self.__SottraiFondo(file_fondo)
        self.__AggiornaIsto()
        
    def Fit1Gauss(self, min, max):
        """Effettua un fit con una gaussiana fra min e max"""
        gauss=ROOT.TF1("Gaussiana", "gaus", min, max)
        self.isto.Fit(gauss, "R+", "")
        parametri=gauss.GetParameters()
        errori=gauss.GetParErrors()
        return parametri

    def Fit2Gauss(self, min1, max1, min2, max2):
        """Effettua il fit con 2 gaussiane; ciascuna viene fittata entro i suoi estremi e poi
        la funzione somma viene fittata fra min1 e max2. Restituisce solo i parametri della
        sunzione fianle."""
        parametri_tot=array( 'd', 6*[0.] )
        gauss1=ROOT.TF1("Gaussiana1", "gaus", min1, max1)
        gauss2=ROOT.TF1("Gaussiana2", "gaus", min2, max2)
        somma=ROOT.TF1("Somma", "gaus(0)+gaus(3)", min1, max2)
        self.isto.Fit(gauss1, "R+", "")
        parametri_g1=gauss1.GetParameters()
        self.isto.Fit(gauss2, "R+", "")
        parametri_g2=gauss2.GetParameters()
        for i in range(3):
                parametri_tot[i]=parametri_g1[i]
                parametri_tot[i+3]=parametri_g2[i]
        somma.SetParameters(parametri_tot)
        somma.SetParNames("costL","mediaL","sigmaL","costH","mediaH","sigmaH")
        self.isto.Fit(somma, "R+", "")
        parametri_tot=somma.GetParameters()
        errori=somma.GetParErrors()
        return parametri_tot

    def Fit4Gauss(self, min1, max1, min2, max2,min3,max3,min4,max4):
        """Effettua il fit con 4 gaussiane; ciascuna viene fittata entro i suoi estremi e poi
        la funzione somma viene fittata fra min1 e max2. Restituisce solo i parametri della
        sunzione fianle."""
        parametri_tot=array( 'd', 12*[0.] )
        gauss1=ROOT.TF1("Gaussiana1", "gaus", min1, max1)
        gauss2=ROOT.TF1("Gaussiana2", "gaus", min2, max2)
        gauss3=ROOT.TF1("Gaussiana3", "gaus", min3, max3)
        gauss4=ROOT.TF1("Gaussiana4", "gaus", min4, max4)
        somma=ROOT.TF1("Somma", "gaus(0)+gaus(3)+gaus(6)+gaus(9)", min1, max4)
        self.isto.Fit(gauss1, "R+", "")
        parametri_g1=gauss1.GetParameters()
        self.isto.Fit(gauss2, "R+", "")
        parametri_g2=gauss2.GetParameters()
        self.isto.Fit(gauss3, "R+", "")
        parametri_g3=gauss3.GetParameters()
        self.isto.Fit(gauss4, "R+", "")
        parametri_g4=gauss4.GetParameters()
        for i in range(3):
                parametri_tot[i]=parametri_g1[i]
                parametri_tot[i+3]=parametri_g2[i]
                parametri_tot[i+6] = parametri_g3[i]
                parametri_tot[i+9] = parametri_g4[i]
        somma.SetParameters(parametri_tot)
        somma.SetParNames("cost1","media1","sigma1","cost2","media2","sigma2","cost3","media3","sigma3","cost4","media4")
        somma.SetParName(11,"sigma4")
        self.isto.Fit(somma, "R+", "")
        parametri_tot=somma.GetParameters()
        errori=somma.GetParErrors()
        return parametri_tot 

    def Disegna(self, min=0, max=False, file=False):
        """Produce il grafico a video, fra il minimo e il massimo opzionali, se il
        parametro file è un nome di file, la canvas viene salvata."""
        if max == False:
            max=self.n_chan
        self.isto.GetXaxis().SetRange(min, max)
        self.isto.GetXaxis().SetTitle('Energie (keV)')
        self.isto.GetXaxis().CenterTitle()
        self.isto.GetYaxis().SetTitle('Conteggio MCA')
        self.isto.GetYaxis().CenterTitle()
        self.canvas.Draw()
        self.isto.Draw()
        if file:
            self.canvas.SaveAs(file)
    
    def __SottraiFondo(self, file_fondo):
        """METODO PRIVATO"""
        file=open(file_fondo, errors='ignore')
        righe=file.readlines()
        file.close()
        inizio=righe.index("<<DATA>>\n") + 1
        fine=righe.index("<<END>>\n")
        """questi sono gli indici del primo bin e dell'ultimo"""
        if fine-inizio !=self.n_chan:
            print("Attenzione! Fondo e spettro hanno un diverso numero di canali!")
        if "GAIA=2;    Analog Gain Index\n" in righe:
            scala_fondo=10
            """Questo è il fondoscala in V dello spettro"""
        else:
            scala_fondo=1
        if scala_fondo != self.scala:
            print("Attenzione! La sccala del fondo è diversa da quella dei dati!")
        fondo=list(map(int, righe[inizio:fine]))
        for i in range(len(fondo)):
            self.spettro[i]-=fondo[i]
        
    def __AggiornaIsto(self):
        """METODO PRIVATO"""
        for i in range(len(self.spettro)):
            self.isto.SetBinContent(i+1, self.spettro[i])

#Fondo = Istogramma('/home/jack/Lab5/Fondo_Identificazione/Fondo_15min_800V.mca')
Fondo = Istogramma('/home/jack/Lab5/Fondo_Identificazione/fondo_nai_up(1)_90_min.mca')
Fondo.isto.SetTitle('Spettro Fondo')
Fondo.Disegna(file='Spettro Fondo.pdf')
Exp1 = ROOT.TF1("Esponenziale", "expo", 145, 220)
#Exp2 = ROOT.TF1("Esponenziale", "expo", 270, 340)
Exp3 = ROOT.TF1("Esponenziale", "expo", 400, 450)
Param_Fondo=[]
estremi=[(230, 260), (340, 390), (500, 550), (575, 650), (750, 820), (870, 1000), (1080, 1160), (1200, 1300), (1375, 1520), (1560, 1610), (1700, 1900), (1925, 2125), (2180, 2350)]
#   (420, 540),  (280, 320),
for est in estremi:
    Param_Fondo.append( Fondo.Fit1Gauss( est[0], est[1] ) )
Fondo.isto.Fit(Exp1, "R+", "")
Fondo.isto.Fit(Exp3, "R+", "")
Param_expo1 = Exp1.GetParameters()
Param_expo3 = Exp3.GetParameters()
Parametri_Totali = array( 'd', (len(estremi)*3+4)*[0.] )
Parametri_Totali[0] = Param_expo1[0]
Parametri_Totali[1] = Param_expo1[1]
Parametri_Totali[2] = Param_expo3[0]
Parametri_Totali[3] = Param_expo3[1]
for i in range( len( Param_Fondo ) ):
    for j in range(3):
        Parametri_Totali[i*3+j+4]=Param_Fondo[i][j]

totale=ROOT.TF1("Somma", "expo(0)+expo(2)+gaus(4)+gaus(7)+gaus(10)+gaus(13)+gaus(16)+gaus(19)+gaus(22)+gaus(25)+gaus(28)+gaus(31)+gaus(34)+gaus(37)+gaus(40)", 145,2350)
totale.SetParameters(Parametri_Totali)
totale.SetParName(0, "Const_e1")
totale.SetParName(1, "Slope_e1")
#totale.SetParLimits(0, Parametri_Totali[0]*0.9, Parametri_Totali[0]*1.1)
#totale.SetParLimits(1, Parametri_Totali[1]*0.9, Parametri_Totali[1]*1.1)
totale.SetParName(2, "Const_e2")
totale.SetParName(3, "Slope_e2")
#totale.SetParLimits(2, Parametri_Totali[2]*0.9, Parametri_Totali[2]*1.1)
#totale.SetParLimits(3, Parametri_Totali[3]*0.9, Parametri_Totali[3]*1.1)
#totale.SetParName(2, "Const_e3")
#totale.SetParName(3, "Slope_e3")
for i in range( len( Param_Fondo ) ):
    totale.SetParName(i*3+4, "Const_g"+str(i+1))
    totale.SetParName(i*3+5, "Mean_g"+str(i+1))
    totale.SetParName(i*3+6, "Sigma_g"+str(i+1))
    #totale.SetParLimits(i*3+4, Parametri_Totali[i*3+4]*0.4, Parametri_Totali[i*3+4]*1.1 )
    #if i>1:
    totale.SetParLimits(i*3+5, Parametri_Totali[i*3+5]-50, Parametri_Totali[i*3+5]+50)
    #totale.SetParLimits(i*3+6, Parametri_Totali[i*3+6]*0.9, Parametri_Totali[i*3+6]*1.1)
Fondo.isto.Fit(totale, "R", "")

expo_basso1 = ROOT.TF1("Esponenziale", "expo", 50, 80)
Fondo.isto.Fit (expo_basso1, "R+", "")
p_expo_basso1 = expo_basso1.GetParameters()
#expo_basso2 = ROOT.TF1("Esponenziale", "expo", 14, 25)
#Fondo.isto.Fit (expo_basso2, "R+", "")
#p_expo_basso2 = expo_basso2.GetParameters()
gauss_basso = Fondo.Fit1Gauss(27, 39)
para_basso = array('d', [p_expo_basso1[0], p_expo_basso1[1], gauss_basso[0], gauss_basso[1], gauss_basso[2], 300])
totale_basso = ROOT.TF1( "Basso", "expo(0)+gaus(2)+[5]", 15, 80)
totale_basso.SetParNames("Const_e1", "Slope_e1", "Const_g", "Mean_g", "Sigma_g", "Costante")
totale_basso.SetParameters (para_basso)
totale_basso.SetParLimits (3, gauss_basso[1]-10, gauss_basso[1]+15)
Fondo.isto.Fit(totale_basso, "R+", "")

input("Premere un tasto per terminare")