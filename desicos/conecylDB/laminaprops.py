# orthotropic
# laminaprop = (e11, e22, nu12, g12, g13, g23)

# isotropic
# laminaprop = (e, e, nu) for ISOTROPIC

def Msi2MPa(value):
    return value * 6895.

laminaprops = {
            'mat_huehne_2008':
                (125.774e3, 10.03e3, 0.271, 5.555e3, 5.555e3,    3.4e3),
            'degenhardt_2010_IM78552_cocomat':
                (142.5e3  ,   8.7e3,  0.28,   5.1e3,   5.1e3,    5.1e3),
            'degenhardt_2010_IM78552_isa':
                (157.4e3  ,   8.6e3,  0.28,   5.3e3,   5.3e3,    5.3e3),
            'degenhardt_2010_IM78552_posicoss':
                (146.5e3  ,   9.7e3,  0.31,   6.1e3,   6.1e3,    6.1e3),
            'M40J/977-2':
                (142.5e3  ,   8.7e3,  0.28,   5.1e3,   5.1e3,    5.1e3),
            'geier_1997':
                (123.55e3 , 8.708e3,  0.319, 5.695e3, 5.695e3, 3.4e3),
            'geier_2002':
                (123.55e3 , 8.708e3,  0.319, 5.695e3, 5.695e3, 5.695e3),
            'mat_huehne_2008':
                (125.774e3, 10.03e3, 0.271, 5.555e3, 5.555e3,    3.4e3),
            'degenhardt_2010_IM78552_cocomat':
                (142.5e3  ,   8.7e3,  0.28,   5.1e3,   5.1e3,    5.1e3),
            'degenhardt_2010_IM78552_isa':
                (157.4e3  ,   8.6e3,  0.28,   5.3e3,   5.3e3,    5.3e3),
            'degenhardt_2010_IM78552_posicoss':
                (146.5e3  ,   9.7e3,  0.31,   6.1e3,   6.1e3,    6.1e3),
            'M40J/977-2':
                (142.5e3  ,   8.7e3,  0.28,   5.1e3,   5.1e3,    5.1e3),
            'geier_1997':
                (123.55e3 , 8.708e3,  0.319, 5.695e3, 5.695e3, 3.4e3),
            'geier_2002':
                (123.55e3 , 8.708e3,  0.319, 5.695e3, 5.695e3, 5.695e3),
            'aisi_304_from_asm_aerospace': (196.5e3, 196.5e3, 0.29),
            'sosa_2006_steel': (206.e3, 206.e3,  0.3),
            'efre_2014': (91.65e3, 6.39e3, 0.34, 3.63e3, 3.63e3, 3.63e3),
            'hilburger_2002':\
                 (Msi2MPa(19.5), Msi2MPa(1.45), 0.30, Msi2MPa(0.813), Msi2MPa(0.813), Msi2MPa(0.813)),
            'hilburger_2004':\
                 (Msi2MPa(18.5), Msi2MPa(1.64), 0.30, Msi2MPa(0.87), Msi2MPa(0.87), Msi2MPa(0.87)),
            'hilburger_2014_AlLi': (71000, 71000, 0.33),
            }
