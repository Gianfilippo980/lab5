import ROOT
from array import array

"""Questioni Stilistiche"""
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptFit(1)
#ROOT.gStyle.SetTitleAlign(4)

class Istogramma:
    """Incapsulatore per l'istogramma di Root"""

    def __init__ (self, file_dati, file_fondo=False):
        """L'argomento file_fondo è optional, se non specificato, il fondo può essere sottratto con
        una successuva operazione"""
        self.canvas=ROOT.TCanvas()
        file=open(file_dati, errors='ignore')
        righe=file.readlines()
        file.close()
        inizio=righe.index("<<DATA>>\n") + 1
        fine=righe.index("<<END>>\n")
        self.n_chan=fine-inizio
        self.isto=ROOT.TH1F(file_dati, file_dati, self.n_chan, 0, self.n_chan)
        self.isto.GetXaxis().SetTitle('Canale MCA')
        self.isto.GetXaxis().CenterTitle()
        self.isto.GetYaxis().SetTitle('Conteggio MCA')
        self.isto.GetYaxis().CenterTitle()
        """questi sono gli indici del primo bin e dell'ultimo"""
        if "GAIA=2;    Analog Gain Index\n" in righe:
            self.scala=10
            """Questo è il fondoscala in V dello spettro"""
        else:
            self.scala=1
        self.spettro=list(map(int, righe[inizio:fine]))
        if file_fondo:
            self.__SottraiFondo(file_fondo)
        for riga in righe:
            parole=riga.split('-')
            if parole[0] == 'REAL_TIME ':
                self.durata=float(parole[1])
                break
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

    def FitExp (self, min, max):
        """Effettua un fit esponenziale fra minimo e massimo, restituisce i parametri"""
        exp=ROOT.TF1("Esponenziale", "expo", min, max)
        self.isto.fit(exp, "R+", "")
        parametri=exp.GetParameters()
        errori=exp.GetParErrors()
        return parametri

    def FitExpGauss (self, minGaus, maxGaus, minExp, maxExp, minTot=False, maxTot=False):
        """Effettua un fit esponenziale fra minExp e maxExp, gaussiano fra minGaus e maxGaus,
        poi effettua un fit con la somma delle due funzioni sul range dell minTot-maxTot.
        Se minTot o maxTot non sono specificati, utlizza gli estremi dell'esponenziale"""
        array( 'd', 5*[0.] )
        """Effettuo i fit separatamente"""
        param_exp = self.FitExp(minExp, maxExp)
        param_gauss = self.Fit1Gauss(minGaus, maxGaus)
        if not(minTot):
            minTot = minExp
        if not(maxTot):
            maxTot = maxExp
        somma = ROOT.TF1("Somma", "gauss(0)+expo(3)", minTot, maxTot)
        somma.SetParNames("CostG", "MediaG", "SigmaG", "CostE", "PendE")
        """Trapianto i parametri"""
        for i in range(3):
            param_tot[i] = param_gauss[i]
        for i in range(2):
            param_tot[i+2] = param_exp[i]            
        somma.SetParameters(param_tot)
        """Fitto con la funzione totale, partendo dai parametri trapiantati"""
        self.isto.Fit(somma, "R+", "")
        param_tot = somma.GetParameters()
        error_tot = somma.GetParErrors()
        return param_tot

    def Scala (self, c_angolare=2.95, intercetta=-14.91):
        """Utilizzare questo metodo per scalare l'asse dell'istogramma alle energie
        i parametri sono riferiti ad un fit lineare canale vs energia fatto in precedeza."""
        fondo=(self.n_chan-intercetta)/c_angolare
        orologio.isto.GetXaxis().SetLimits(intercetta, fondo)
        orologio.isto.GetXaxis().SetTitle('Energia (keV)')


    def Disegna(self, min=0, max=False, file=False):
        """Produce il grafico a video, fra il minimo e il massimo opzionali, se il
        parametro file è un nome di file, la canvas viene salvata."""
        if max == False:
            max=self.n_chan
        self.isto.GetXaxis().SetRange(min, max)
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
        for riga in righe:
            parole=riga.split('-')
            if parole[0] == 'REAL_TIME ':
                durata_fondo=float(parole[1])
                break
        if durata_fondo != self.durata:
            print ("Attenzione! Il fondo ha una ")
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