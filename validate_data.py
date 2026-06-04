"""
Script de validação — verifica que todos os módulos funcionam
e que os cálculos produzem resultados corretos.
"""
import sys
sys.path.insert(0, ".")

from src.config import DATA_RAW, QUAL_VARS, CONT_VARS, AGE_BINS, AGE_LABELS
from src.data_loader import load_raw, load_subsets
from src.frequency_tables import freq_table_qualitative, freq_table_classes, sturges_k
from src.descriptive_stats import descriptive_summary, pearson2_skewness, descriptive_by_group

print("=" * 60)
print("VALIDAÇÃO DO PROJETO")
print("=" * 60)

# 1. Carga e subsets
print("\n[1] Carga dos dados...")
data = load_subsets()
df_full = data["df_full"]
df_chol = data["df_chol"]
df_bp = data["df_bp"]

assert df_full.shape[0] == 918, f"ERRO: df_full tem {df_full.shape[0]} linhas"
assert df_chol.shape[0] == 746, f"ERRO: df_chol tem {df_chol.shape[0]} linhas"
assert df_bp.shape[0] == 917, f"ERRO: df_bp tem {df_bp.shape[0]} linhas"
print(f"  ✓ df_full: {df_full.shape[0]} linhas")
print(f"  ✓ df_chol: {df_chol.shape[0]} linhas")
print(f"  ✓ df_bp:   {df_bp.shape[0]} linhas")

# 2. HeartDisease
hd = df_full["HeartDisease"].value_counts()
assert hd[1] == 508, f"ERRO: HeartDisease=1 tem {hd[1]}"
assert hd[0] == 410, f"ERRO: HeartDisease=0 tem {hd[0]}"
print(f"\n[2] HeartDisease:")
print(f"  ✓ Com doença: {hd[1]} (55.3%)")
print(f"  ✓ Sem doença: {hd[0]} (44.7%)")

# 3. Tabelas de frequência qualitativas
print(f"\n[3] Tabelas de frequência qualitativas...")
for var in QUAL_VARS:
    ft = freq_table_qualitative(df_full[var])
    assert ft["fi"].sum() == 918, f"ERRO: soma fi de {var} ≠ 918"
    assert abs(ft["fri (%)"].sum() - 100.0) < 0.1, f"ERRO: soma fri de {var} ≠ 100%"
print(f"  ✓ Todas as 6 variáveis validadas (soma fi = 918, soma fri ≈ 100%)")

# 4. Tabela de frequências de Age (faixas etárias)
print(f"\n[4] Tabela de frequências de Age (faixas)...")
ft_age = freq_table_classes(df_full["Age"], bins=AGE_BINS, labels=AGE_LABELS)
assert ft_age["fi"].sum() == 918, f"ERRO: soma fi de Age ≠ 918"
print(f"  ✓ Soma fi = {ft_age['fi'].sum()}")
print(f"  Distribuição: {dict(ft_age['fi'])}")

# 5. Medidas descritivas de Age (valores brutos)
print(f"\n[5] Medidas descritivas de Age (valores brutos, n=918)...")
desc = descriptive_summary(df_full["Age"], name="Age")
print(f"  Média: {desc.loc['Média'].values[0]}")
print(f"  Mediana: {desc.loc['Mediana'].values[0]}")
print(f"  Desvio-padrão: {desc.loc['Desvio-padrão (σ)'].values[0]}")
as_age = pearson2_skewness(df_full["Age"])
print(f"  Assimetria (Pearson 2): {as_age:.4f}")
print(f"  ✓ Calculado sobre valores brutos (não agrupados)")

# 6. Sturges
print(f"\n[6] Regra de Sturges...")
k918 = sturges_k(918)
k746 = sturges_k(746)
k917 = sturges_k(917)
print(f"  n=918 → k={k918}")
print(f"  n=746 → k={k746}")
print(f"  n=917 → k={k917}")

# 7. Descritivas por grupo
print(f"\n[7] Descritivas por grupo (Age)...")
desc_grp = descriptive_by_group(df_full, "Age")
print(desc_grp)

# 8. Pearson 2 para Oldpeak
print(f"\n[8] Pearson 2 para Oldpeak...")
as_old = pearson2_skewness(df_full["Oldpeak"])
print(f"  Assimetria (Pearson 2): {as_old:.4f}")
print(f"  {'Positiva (cauda à direita)' if as_old > 0 else 'Negativa'}")

print(f"\n{'=' * 60}")
print("TODAS AS VALIDAÇÕES PASSARAM ✓")
print(f"{'=' * 60}")
