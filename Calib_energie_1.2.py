"""Questo programma serve a fare i fit su un piccolo numero di dati,
con impostazioni molto diverse fra loro, quindi fatti uno per votlta a mano"""
import ROOT
from array import array

n_chan=8192
"""Numero di bins dell'MCA"""

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
            self.SottraiFondo(file_fondo)
        self.AggiornaIsto()

    def SottraiFondo(self, file_fondo):
        """Utilizzare questo metodo per effetture la sottrazione fra due spettri
        con lo stesso nuemro di canali e la stessa scala"""
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
        
    def AggiornaIsto(self):
        """sposta qualunque cosa sia in spettro nell'istogramma di ROOT"""
        for i in range(len(self.spettro)):
            self.isto.SetBinContent(i+1, self.spettro[i])
    
    def Fit1Gauss(self, min, max):
        """Effettua un fit con una gaussiana fra min e max, restituisce la media"""
        gauss=ROOT.TF1("Gaussiana", "gaus", min, max)
        self.isto.Fit(gauss, "R+", "")
        parametri=gauss.GetParameters()
        errori=gauss.GetParErrors()
        return parametri

    def Fit2Gauss(self, min1, max1, min2, max2):
        """Effettua il fit con 2 gaussiane, resituisce le deu medie"""
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
        """Produce il grafico a video, fra il minimo e il massimo opzionali, volendo salva il file
        per esportare l'immagine"""
        self.isto.GetXaxis().SetRange(min, max)
        self.canvas.Draw()
        self.isto.Draw()
        if file:
            self.canvas.SaveAs(file)

"""Creo una lista in cui conservare i valori delle posizioni dei picchi"""
picchi=[]
"""E una tupla per i valori delle energie, ordine crescente"""
energie=(1,2,3)
file_fondo = 'fondo_800V_240s.mca'

"""Adesso basterà istanziare la classe per ogni spettro, si può accedere direttametne al canvas
con il nome.canvas o all'istogramma con nome.isto..."""

cobalto=Istogramma('Cobalto_800V_240s.mca', file_fondo)
param_cobalto = cobalto.Fit2Gauss(3250, 3550, 3800, 4000)
picchi.append(param_cobalto[1])
picchi.append(param_cobalto[4])
cobalto.Disegna(3000, 4500)

cesio=Istogramma('Cesio_800V_240s.mca')
param_cesio = cesio.Fit1Gauss(1800, 2050)
picchi.append(param_cesio[1])
cesio.Disegna(1600, 2300, 'cesio_800V_240s.pdf')

potassio=Istogramma('Potassio_800V_240s.mca')
potassio.Fit1Gauss(4000, 5000)
potassio.Fit1Gauss(50, 1000)
potassio.Disegna()


"""Alla fine mettiamo la parte ceh fa il grafico cartesiano di picchi ed energie"""
picchi.sort()
"""Li metto in ordine crescente"""
canvas_cart=ROOT.TCanvas()
n=len(energie)
x=array('d', energie)
y=array('d', picchi)
graf_cart=ROOT.TGraph(n, x, y)
graf_cart.SetLineWidth( 0 )
graf_cart.SetMarkerColor( 4 )
graf_cart.SetMarkerStyle( 20 )
graf_cart.SetTitle( 'Calibrazione' )
graf_cart.GetXaxis().SetTitle( 'Energie (keV)' )
graf_cart.GetYaxis().SetTitle( 'Picco (#MCA)' )
graf_cart.Draw( 'ACP' )
canvas_cart.Update()
canvas_cart.GetFrame().SetBorderSize( 12 )
canvas_cart.Modified()
canvas_cart.Update()
input("premere un tasto per terminare")