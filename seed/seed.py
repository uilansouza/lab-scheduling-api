"""
Seed script — inserts 100+ synthetic exam records.
Run: python -m seed.seed
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal
from app.models.exam import Exam

EXAMS = [
    # Hematology
    ("EXM-0001", "Hemograma Completo Sintético", "Contagem de células sanguíneas e diferencial", "HEMATOLOGY"),
    ("EXM-0002", "Eritrograma Sintético", "Análise da série vermelha", "HEMATOLOGY"),
    ("EXM-0003", "Leucograma Sintético", "Contagem e diferencial de leucócitos", "HEMATOLOGY"),
    ("EXM-0004", "Plaquetograma Sintético", "Contagem e morfologia plaquetária", "HEMATOLOGY"),
    ("EXM-0005", "Reticulócitos Sintéticos", "Contagem de reticulócitos em percentagem e valor absoluto", "HEMATOLOGY"),
    ("EXM-0006", "Velocidade de Hemossedimentação Sintética", "VHS em mm/h", "HEMATOLOGY"),
    ("EXM-0007", "Tempo de Protrombina Sintético", "TP e INR", "HEMATOLOGY"),
    ("EXM-0008", "Tempo de Tromboplastina Parcial Sintético", "TTPA e relação", "HEMATOLOGY"),
    ("EXM-0009", "Fibrinogênio Sintético", "Dosagem funcional de fibrinogênio", "HEMATOLOGY"),
    ("EXM-0010", "D-Dímero Sintético", "Marcador de fibrinólise", "HEMATOLOGY"),
    # Biochemistry
    ("EXM-0011", "Glicose em Jejum Sintética", "Glicemia de jejum plasmática", "BIOCHEMISTRY"),
    ("EXM-0012", "Hemoglobina Glicada Sintética", "HbA1c por HPLC", "BIOCHEMISTRY"),
    ("EXM-0013", "Ureia Sintética", "Dosagem sérica de ureia", "BIOCHEMISTRY"),
    ("EXM-0014", "Creatinina Sintética", "Dosagem sérica de creatinina", "BIOCHEMISTRY"),
    ("EXM-0015", "Taxa de Filtração Glomerular Sintética", "TFG estimada pela fórmula CKD-EPI", "BIOCHEMISTRY"),
    ("EXM-0016", "Ácido Úrico Sintético", "Dosagem sérica de ácido úrico", "BIOCHEMISTRY"),
    ("EXM-0017", "Proteínas Totais Sintéticas", "Proteínas totais e frações", "BIOCHEMISTRY"),
    ("EXM-0018", "Albumina Sintética", "Dosagem sérica de albumina", "BIOCHEMISTRY"),
    ("EXM-0019", "Bilirrubinas Sintéticas", "Bilirrubina total, direta e indireta", "BIOCHEMISTRY"),
    ("EXM-0020", "Fosfatase Alcalina Sintética", "FA sérica", "BIOCHEMISTRY"),
    ("EXM-0021", "Gamaglutamiltransferase Sintética", "GGT sérica", "BIOCHEMISTRY"),
    ("EXM-0022", "Aspartato Aminotransferase Sintética", "AST/TGO sérica", "BIOCHEMISTRY"),
    ("EXM-0023", "Alanina Aminotransferase Sintética", "ALT/TGP sérica", "BIOCHEMISTRY"),
    ("EXM-0024", "Desidrogenase Láctica Sintética", "LDH sérica total", "BIOCHEMISTRY"),
    ("EXM-0025", "Creatinofosfoquinase Sintética", "CPK total sérica", "BIOCHEMISTRY"),
    ("EXM-0026", "CPK-MB Sintética", "Fração MB da CPK", "BIOCHEMISTRY"),
    ("EXM-0027", "Troponina I Sintética", "Troponina I de alta sensibilidade", "BIOCHEMISTRY"),
    ("EXM-0028", "Mioglobina Sintética", "Dosagem sérica de mioglobina", "BIOCHEMISTRY"),
    ("EXM-0029", "Colesterol Total Sintético", "Dosagem sérica de colesterol total", "BIOCHEMISTRY"),
    ("EXM-0030", "HDL Colesterol Sintético", "Fração HDL do colesterol", "BIOCHEMISTRY"),
    ("EXM-0031", "LDL Colesterol Sintético", "Fração LDL calculada por Friedewald", "BIOCHEMISTRY"),
    ("EXM-0032", "VLDL Colesterol Sintético", "Fração VLDL estimada", "BIOCHEMISTRY"),
    ("EXM-0033", "Triglicerídeos Sintéticos", "Dosagem sérica de triglicerídeos", "BIOCHEMISTRY"),
    ("EXM-0034", "Ferro Sérico Sintético", "Dosagem de ferro sérico", "BIOCHEMISTRY"),
    ("EXM-0035", "Ferritina Sintética", "Dosagem sérica de ferritina", "BIOCHEMISTRY"),
    ("EXM-0036", "Transferrina Sintética", "Dosagem sérica de transferrina", "BIOCHEMISTRY"),
    ("EXM-0037", "Capacidade de Ligação do Ferro Sintética", "TIBC e UIBC", "BIOCHEMISTRY"),
    ("EXM-0038", "Cálcio Total Sintético", "Dosagem sérica de cálcio total", "BIOCHEMISTRY"),
    ("EXM-0039", "Fósforo Sintético", "Dosagem sérica de fósforo inorgânico", "BIOCHEMISTRY"),
    ("EXM-0040", "Magnésio Sintético", "Dosagem sérica de magnésio", "BIOCHEMISTRY"),
    # Hormones
    ("EXM-0041", "TSH Sintético", "Hormônio tireoestimulante ultrassensível", "ENDOCRINOLOGY"),
    ("EXM-0042", "T4 Livre Sintético", "Tiroxina livre sérica", "ENDOCRINOLOGY"),
    ("EXM-0043", "T3 Total Sintético", "Tri-iodotironina total sérica", "ENDOCRINOLOGY"),
    ("EXM-0044", "Anti-TPO Sintético", "Anticorpo antitireoperoxidase", "ENDOCRINOLOGY"),
    ("EXM-0045", "Anti-Tireoglobulina Sintético", "Anticorpo antitireoglobulina", "ENDOCRINOLOGY"),
    ("EXM-0046", "Cortisol Basal Sintético", "Cortisol sérico às 8h", "ENDOCRINOLOGY"),
    ("EXM-0047", "Insulina Sintética", "Dosagem sérica de insulina em jejum", "ENDOCRINOLOGY"),
    ("EXM-0048", "Peptídeo C Sintético", "Dosagem sérica do peptídeo C", "ENDOCRINOLOGY"),
    ("EXM-0049", "Prolactina Sintética", "Dosagem sérica de prolactina", "ENDOCRINOLOGY"),
    ("EXM-0050", "LH Sintético", "Hormônio luteinizante sérico", "ENDOCRINOLOGY"),
    ("EXM-0051", "FSH Sintético", "Hormônio folículo-estimulante sérico", "ENDOCRINOLOGY"),
    ("EXM-0052", "Estradiol Sintético", "Dosagem sérica de estradiol", "ENDOCRINOLOGY"),
    ("EXM-0053", "Progesterona Sintética", "Dosagem sérica de progesterona", "ENDOCRINOLOGY"),
    ("EXM-0054", "Testosterona Total Sintética", "Dosagem sérica de testosterona total", "ENDOCRINOLOGY"),
    ("EXM-0055", "DHEA-S Sintético", "Sulfato de deidroepiandrosterona sérico", "ENDOCRINOLOGY"),
    ("EXM-0056", "PTH Intacto Sintético", "Paratormônio intacto sérico", "ENDOCRINOLOGY"),
    ("EXM-0057", "Vitamina D 25-OH Sintética", "25-hidroxivitamina D sérica", "ENDOCRINOLOGY"),
    ("EXM-0058", "GH Basal Sintético", "Hormônio do crescimento basal", "ENDOCRINOLOGY"),
    ("EXM-0059", "IGF-1 Sintético", "Fator de crescimento semelhante à insulina tipo 1", "ENDOCRINOLOGY"),
    ("EXM-0060", "Aldosterona Sintética", "Dosagem sérica de aldosterona", "ENDOCRINOLOGY"),
    # Immunology / Serology
    ("EXM-0061", "PCR Ultrassensível Sintético", "Proteína C reativa de alta sensibilidade", "IMMUNOLOGY"),
    ("EXM-0062", "Fator Reumatoide Sintético", "FR quantitativo sérico", "IMMUNOLOGY"),
    ("EXM-0063", "Anti-CCP Sintético", "Anticorpo antipeptídeo citrulinado cíclico", "IMMUNOLOGY"),
    ("EXM-0064", "FAN Sintético", "Fator antinúcleo — triagem por IFI", "IMMUNOLOGY"),
    ("EXM-0065", "Anti-DNA Nativo Sintético", "Anticorpo anti-dsDNA quantitativo", "IMMUNOLOGY"),
    ("EXM-0066", "Complemento C3 Sintético", "Dosagem sérica do complemento C3", "IMMUNOLOGY"),
    ("EXM-0067", "Complemento C4 Sintético", "Dosagem sérica do complemento C4", "IMMUNOLOGY"),
    ("EXM-0068", "IgG Total Sintética", "Imunoglobulina G sérica total", "IMMUNOLOGY"),
    ("EXM-0069", "IgA Total Sintética", "Imunoglobulina A sérica total", "IMMUNOLOGY"),
    ("EXM-0070", "IgM Total Sintética", "Imunoglobulina M sérica total", "IMMUNOLOGY"),
    ("EXM-0071", "IgE Total Sintética", "Imunoglobulina E sérica total", "IMMUNOLOGY"),
    ("EXM-0072", "Beta-2 Microglobulina Sintética", "Dosagem sérica de beta-2 microglobulina", "IMMUNOLOGY"),
    ("EXM-0073", "Procalcitonina Sintética", "Marcador de sepse bacteriana", "IMMUNOLOGY"),
    ("EXM-0074", "Interleucina-6 Sintética", "IL-6 sérica — marcador inflamatório", "IMMUNOLOGY"),
    ("EXM-0075", "Anti-Cardiolipina IgG Sintético", "Anticorpo anticardiolipina IgG", "IMMUNOLOGY"),
    # Microbiology / Serology Infectious
    ("EXM-0076", "Sorol. Hepatite B — HBsAg Sintético", "Antígeno de superfície do HBV", "MICROBIOLOGY"),
    ("EXM-0077", "Sorol. Hepatite B — Anti-HBs Sintético", "Anticorpo anti-HBsAg", "MICROBIOLOGY"),
    ("EXM-0078", "Sorol. Hepatite C — Anti-HCV Sintético", "Anticorpo anti-HCV triagem", "MICROBIOLOGY"),
    ("EXM-0079", "Sorol. HIV — Ag/Ac Sintético", "Teste combinado Ag p24 + anticorpo HIV", "MICROBIOLOGY"),
    ("EXM-0080", "VDRL Sintético", "Triagem sorológica para sífilis", "MICROBIOLOGY"),
    ("EXM-0081", "FTA-ABS Sintético", "Confirmação sorológica de sífilis", "MICROBIOLOGY"),
    ("EXM-0082", "Sorol. Toxoplasmose IgG Sintético", "IgG anti-Toxoplasma gondii", "MICROBIOLOGY"),
    ("EXM-0083", "Sorol. Toxoplasmose IgM Sintético", "IgM anti-Toxoplasma gondii", "MICROBIOLOGY"),
    ("EXM-0084", "Sorol. CMV IgG Sintético", "IgG anti-citomegalovírus", "MICROBIOLOGY"),
    ("EXM-0085", "Sorol. Rubéola IgG Sintético", "IgG anti-rubéola", "MICROBIOLOGY"),
    # Urinalysis
    ("EXM-0086", "Urina Tipo I Sintética", "Exame de urina rotina (EAS)", "URINALYSIS"),
    ("EXM-0087", "Urocultura Sintética", "Cultura de urina com antibiograma", "URINALYSIS"),
    ("EXM-0088", "Microalbuminúria Sintética", "Albumina urinária em amostra isolada", "URINALYSIS"),
    ("EXM-0089", "Creatinina Urinária Sintética", "Dosagem de creatinina em amostra de urina", "URINALYSIS"),
    ("EXM-0090", "Proteína Urinária 24h Sintética", "Proteinúria em urina de 24 horas", "URINALYSIS"),
    # Tumor markers
    ("EXM-0091", "PSA Total Sintético", "Antígeno prostático específico total", "ONCOLOGY"),
    ("EXM-0092", "PSA Livre Sintético", "Antígeno prostático específico livre", "ONCOLOGY"),
    ("EXM-0093", "CEA Sintético", "Antígeno carcinoembriônico sérico", "ONCOLOGY"),
    ("EXM-0094", "AFP Sintético", "Alfa-fetoproteína sérica", "ONCOLOGY"),
    ("EXM-0095", "CA 125 Sintético", "Antígeno carboidrato 125", "ONCOLOGY"),
    ("EXM-0096", "CA 19-9 Sintético", "Antígeno carboidrato 19-9", "ONCOLOGY"),
    ("EXM-0097", "CA 15-3 Sintético", "Antígeno carboidrato 15-3", "ONCOLOGY"),
    ("EXM-0098", "Beta-HCG Quantitativo Sintético", "Gonadotrofina coriônica humana quantitativa", "ONCOLOGY"),
    ("EXM-0099", "LDH Isoenzimas Sintéticas", "Desidrogenase láctica com fracionamento", "ONCOLOGY"),
    ("EXM-0100", "Neuron-Specific Enolase Sintética", "NSE sérica — marcador de tumor neuroendócrino", "ONCOLOGY"),
    # Extra exams to exceed 100
    ("EXM-0101", "Homocisteína Sintética", "Dosagem plasmática de homocisteína", "BIOCHEMISTRY"),
    ("EXM-0102", "Vitamina B12 Sintética", "Dosagem sérica de cobalamina", "BIOCHEMISTRY"),
    ("EXM-0103", "Ácido Fólico Sintético", "Dosagem sérica de folato", "BIOCHEMISTRY"),
    ("EXM-0104", "Zinco Sérico Sintético", "Dosagem sérica de zinco", "BIOCHEMISTRY"),
    ("EXM-0105", "Cobre Sérico Sintético", "Dosagem sérica de cobre", "BIOCHEMISTRY"),
    ("EXM-0106", "Amilase Sintética", "Amilase sérica total", "BIOCHEMISTRY"),
    ("EXM-0107", "Lipase Sintética", "Lipase sérica", "BIOCHEMISTRY"),
    ("EXM-0108", "Gasometria Arterial Sintética", "pH, pCO2, pO2, HCO3, BE", "BIOCHEMISTRY"),
    ("EXM-0109", "Lactato Arterial Sintético", "Lactato sérico/arterial", "BIOCHEMISTRY"),
    ("EXM-0110", "BNP Sintético", "Peptídeo natriurético cerebral — marcador cardíaco", "BIOCHEMISTRY"),
]


def run():
    db = SessionLocal()
    try:
        existing = {e.code for e in db.query(Exam).all()}
        new_exams = [
            Exam(code=code, name=name, description=desc, category=cat, active=True)
            for code, name, desc, cat in EXAMS
            if code not in existing
        ]
        if new_exams:
            db.bulk_save_objects(new_exams)
            db.commit()
            print(f"✅ Seeded {len(new_exams)} exams.")
        else:
            print("ℹ️  No new exams to seed.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
