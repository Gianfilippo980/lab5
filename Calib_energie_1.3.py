"""Questo programma serve a fare i fit su un piccolo numero di dati,
con impostazioni molto diverse fra loro, quindi fatti uno per votlta a mano"""
import ROOT
from array import array

n_chan=8192
"""Numero di bins dell'MCA"""
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptFit(1)
#ROOT.gStyle.SetTitleAlign(4)

class Istogramma:
    """Incapsulatore per l'istogramma di Root"""

    def __init__ (self, file_dati, file_fondo=False):
        """L'argomento file_fondo è optional, se non specificato, il fondo può essere sottratto con
        una successuva operazione"""
        self.canvas=ROOT.TCanvas()
        self.isto=ROOT.TH1F(file_dati, file_dati, n_chan, 0, n_chan)
        file=open(file_dati, errors='ignore')
        righe=file.readlines()
        file.close()
        inizio=righe.index("<<DATA>>\n") + 1
        fine=righe.index("<<END>>\n")
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

    def Disegna(self, min=0, max=n_chan, file=False):
        """Produce il grafico a video, fra il minimo e il massimo opzionali, se il
        parametro file è un nome di file, la canvas viene salvata."""
        self.isto.GetXaxis().SetRange(min, max)
        self.isto.GetXaxis().SetTitle('Canale MCA')
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

"""Creo una lista in cui conservare i valori delle posizioni dei picchi"""
picchi=[]
file_fondo = 'fondo_800V_240s.mca'

"""Adesso basterà istanziare la classe per ogni spettro, si può accedere direttametne al canvas
con il nome.canvas o all'istogramma con nome.isto..."""

cobalto=Istogramma('Cobalto_800V_240s.mca', file_fondo)
cobalto.isto.SetTitle('Spettro Cobalto')
param_cobalto = cobalto.Fit2Gauss(3250, 3550, 3800, 4100)
picchi.append(param_cobalto[1])
picchi.append(param_cobalto[4])
cobalto.Disegna(file='cobalto.pdf')

cesio=Istogramma('Cesio_800V_240s.mca', file_fondo)
cesio.isto.SetTitle('Spettro Cesio')
cesio.SottraiFondo('fondo_800V_240s.mca')
param_cesio = cesio.Fit1Gauss(1800, 2050)
picchi.append(param_cesio[1])
cesio.Disegna(file='cesio.pdf')

potassio=Istogramma('Potassio_800V_240s.mca', file_fondo)
potassio.isto.SetTitle('Spettro Potassio')
picchi.append(potassio.Fit1Gauss(4150, 4500)[1])
potassio.Disegna(file='potassio.pdf')

sodio=Istogramma('Sodio_800V_240s.mca', file_fondo)
sodio.isto.SetTitle('Spettro Sodio')
picchi.append(sodio.Fit1Gauss(1400, 1600)[1])
picchi.append(sodio.Fit1Gauss(3550, 3900)[1])
sodio.Disegna(file='sodio.pdf')

"""Alla fine mettiamo la parte ceh fa il grafico cartesiano di picchi ed energie"""
picchi.sort()
Energie_Calibrazione = [511, 1173.2, 1332.5, 661.7, 1460, 1275]
Energie_Calibrazione.sort()
print(Energie_Calibrazione,picchi)
Canvas = ROOT.TCanvas('Calibrazione','Retta di Calibrazione',800,400)
Canvas.SetGrid()
Graph = ROOT.TGraph(len(Energie_Calibrazione),array('d',Energie_Calibrazione),array('d',picchi))
Graph.SetLineWidth(0)
Graph.SetMarkerColor( 4)
Graph.SetMarkerStyle( 20)
Graph.SetMarkerSize(2)
Graph.SetTitle( 'Retta di Calibrazione (800V)')
Graph.GetXaxis().SetTitle( 'Energia (keV)' )
Graph.GetXaxis().CenterTitle()
Graph.GetYaxis().CenterTitle()
Graph.GetYaxis().SetTitle( 'Canale MCA' )
Retta_Fit = ROOT.TF1('Retta',"[0]+[1]*x",0,5)
Retta_Fit.SetLineColor(807)
Retta_Fit.SetLineWidth(2)
Graph.Fit(Retta_Fit)
ROOT.gStyle.SetStatX(0.47)
ROOT.gStyle.SetStatY(0.89)
Coefficiente_Angolare = Retta_Fit.GetParameter(1)
Intercetta = Retta_Fit.GetParameter(0)
Graph.Draw('AP')
Canvas.GetFrame().SetBorderSize(12)
Canvas.Modified()
Canvas.Update()
Canvas.SaveAs('fit_calib_1.pdf')

input("premere un tasto per terminare")