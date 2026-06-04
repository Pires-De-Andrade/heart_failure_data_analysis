$csv = Import-Csv 'dataset\raw\heart.csv'
Write-Host "Total linhas: $($csv.Count)"

$cholZero = ($csv | Where-Object { [int]$_.Cholesterol -eq 0 }).Count
Write-Host "Cholesterol=0: $cholZero"

$bpZero = ($csv | Where-Object { [int]$_.RestingBP -eq 0 }).Count
Write-Host "RestingBP=0: $bpZero"

Write-Host "--- HeartDisease ---"
$csv | Group-Object HeartDisease | ForEach-Object { Write-Host "$($_.Name): $($_.Count)" }

Write-Host "--- Sex ---"
$csv | Group-Object Sex | ForEach-Object { Write-Host "$($_.Name): $($_.Count)" }

Write-Host "--- ChestPainType ---"
$csv | Group-Object ChestPainType | ForEach-Object { Write-Host "$($_.Name): $($_.Count)" }

Write-Host "--- RestingECG ---"
$csv | Group-Object RestingECG | ForEach-Object { Write-Host "$($_.Name): $($_.Count)" }

Write-Host "--- ExerciseAngina ---"
$csv | Group-Object ExerciseAngina | ForEach-Object { Write-Host "$($_.Name): $($_.Count)" }

Write-Host "--- ST_Slope ---"
$csv | Group-Object ST_Slope | ForEach-Object { Write-Host "$($_.Name): $($_.Count)" }

Write-Host "--- FastingBS ---"
$csv | Group-Object FastingBS | ForEach-Object { Write-Host "$($_.Name): $($_.Count)" }

Write-Host "--- Age range ---"
$ages = $csv | ForEach-Object { [int]$_.Age }
Write-Host "Min: $($ages | Measure-Object -Minimum | Select-Object -ExpandProperty Minimum)"
Write-Host "Max: $($ages | Measure-Object -Maximum | Select-Object -ExpandProperty Maximum)"

Write-Host "--- Oldpeak range ---"
$oldpeaks = $csv | ForEach-Object { [double]$_.Oldpeak }
Write-Host "Min: $($oldpeaks | Measure-Object -Minimum | Select-Object -ExpandProperty Minimum)"
Write-Host "Max: $($oldpeaks | Measure-Object -Maximum | Select-Object -ExpandProperty Maximum)"
