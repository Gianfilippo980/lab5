import ROOT
from array import array

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
        self.isto=ROOT.TH1F(file_dati, file_dati, self.n_chan, 0, (self.n_chan - self.intercetta) / self.c_angolare)
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

path='/home/jack/Lab5/calibrazione_800V/'
file_fondo = '/home/jack/Lab5/calibrazione_800V/fondo_800V_240s.mca'
picchi = []
europio = Istogramma(path+'Europio_800V_240s.mca', file_fondo)
europio.isto.SetTitle('Europio')
picchi.append(europio.Fit1Gauss(35, 52)[1])
picchi.append(europio.Fit1Gauss(330, 370)[1])
picchi.append(europio.Fit1Gauss(1349, 1481)[1])
picchi.append(europio.Fit1Gauss(120, 140)[1])
picchi.append(europio.Fit1Gauss(233, 269)[1])
picchi.append(europio.Fit1Gauss(745, 823)[1])
due_gauss = europio.Fit2Gauss(924, 1005, 1059, 1160)
picchi.append(due_gauss[1])
picchi.append(due_gauss[4])
europio.Disegna(file=path+'europio.pdf', max = 1550)
picchi.sort()
print('Energie:')
for picco in picchi:
    print(f"{picco:.4}", 'keV')

input('premere un tasto per terminare')