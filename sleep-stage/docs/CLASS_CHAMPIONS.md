# Class-level champions

Per-class F1, champion = argmax F1 within each (window, subset, class).
Best-recall model listed separately (high-recall expert option).
`bench` = BENCHMARK_30 (237,936 epochs, headline); `valid` = all scored valid epochs.
E17/E18 cover 237,310/237,936 bench epochs (LightGBM gaps); all other runs full.

# BENCHMARK_30 (headline)

## ALL

| Class | Champion | F1 | Recall | Precision | Runner-up | Best recall model |
|---|---|---|---|---|---|---|
| Wake | **Ens 0.7ANY+0.3RSN+bias** (E16) | 0.941 | 0.928 | 0.955 | AnySleep 3ch (E11) 0.941 | YASA crop (E02c) 0.993 |
| N1 | **Ens v2 +bias** (E19b) | 0.638 | 0.691 | 0.592 | Ens v2 ANYx2+USleepCSDP+LGBM (E19) 0.635 | Ens v2 +bias (E19b) 0.691 |
| N2 | **Ens v2 ANYx2+USleepCSDP+LGBM** (E19) | 0.892 | 0.904 | 0.881 | Ens v2 +bias (E19b) 0.891 | Ens v2 ANYx2+USleepCSDP+LGBM (E19) 0.904 |
| N3 | **Ens v2 +bias** (E19b) | 0.833 | 0.830 | 0.837 | Ens v2 ANYx2+USleepCSDP+LGBM (E19) 0.833 | LightGBM (ours) (E00) 0.873 |
| REM | **Ens v2 ANYx2+USleepCSDP+LGBM** (E19) | 0.915 | 0.915 | 0.915 | Ens v2 +bias (E19b) 0.915 | Ens v2 +bias (E19b) 0.918 |

## SC

| Class | Champion | F1 | Recall | Precision | Runner-up | Best recall model |
|---|---|---|---|---|---|---|
| Wake | **Ens 0.7ANY+0.3RSN+bias** (E16) | 0.943 | 0.931 | 0.956 | AnySleep 3ch (E11) 0.943 | YASA crop (E02c) 0.994 |
| N1 | **Ens v2 +bias** (E19b) | 0.624 | 0.691 | 0.569 | Ens v2 ANYx2+USleepCSDP+LGBM (E19) 0.623 | Ens v2 +bias (E19b) 0.691 |
| N2 | **Ens v2 ANYx2+USleepCSDP+LGBM** (E19) | 0.889 | 0.903 | 0.875 | U-Sleep CSDP (open) (E21) 0.887 | U-Sleep CSDP (open) (E21) 0.912 |
| N3 | **Ens v2 +bias** (E19b) | 0.822 | 0.793 | 0.854 | Ens v2 ANYx2+USleepCSDP+LGBM (E19) 0.822 | LightGBM (ours) (E00) 0.865 |
| REM | **U-Sleep CSDP (open)** (E21) | 0.919 | 0.918 | 0.919 | Ens v2 ANYx2+USleepCSDP+LGBM (E19) 0.909 | U-Sleep CSDP (open) (E21) 0.918 |

## ST

| Class | Champion | F1 | Recall | Precision | Runner-up | Best recall model |
|---|---|---|---|---|---|---|
| Wake | **Ens ANYx3+LGBM** (E17) | 0.916 | 0.907 | 0.925 | Ens ANYx3+LGBM+bias (E18) 0.911 | YASA Pz+EOG (E03) 0.993 |
| N1 | **Ens 0.7ANY+0.3RSN+bias** (E16) | 0.745 | 0.742 | 0.748 | Ens ANYx3+LGBM+bias (E18) 0.739 | Ens 0.7ANY+0.3RSN+bias (E16) 0.742 |
| N2 | **AnySleep 3ch** (E11) | 0.921 | 0.924 | 0.917 | Ens 0.7ANY+0.3RSN+bias (E16) 0.919 | AnySleep 3ch (E11) 0.924 |
| N3 | **AnySleep 3ch** (E11) | 0.873 | 0.893 | 0.854 | Ens 0.7ANY+0.3RSN+bias (E16) 0.869 | Ens v2 ANYx2+USleepCSDP+LGBM (E19) 0.904 |
| REM | **AnySleep 3ch** (E11) | 0.949 | 0.954 | 0.945 | Ens 0.7ANY+0.3RSN+bias (E16) 0.948 | AnySleep 3ch (E11) 0.954 |

# FULL-VALID

## ALL

| Class | Champion | F1 | Recall | Precision | Runner-up | Best recall model |
|---|---|---|---|---|---|---|
| Wake | **Ens 0.7ANY+0.3RSN+bias** (E16) | 0.985 | 0.981 | 0.989 | AnySleep 3ch (E11) 0.985 | YASA crop (E02c) 0.993 |
| N1 | **Ens v2 +bias** (E19b) | 0.634 | 0.691 | 0.585 | Ens v2 ANYx2+USleepCSDP+LGBM (E19) 0.632 | Ens v2 +bias (E19b) 0.691 |
| N2 | **Ens v2 ANYx2+USleepCSDP+LGBM** (E19) | 0.892 | 0.904 | 0.880 | Ens v2 +bias (E19b) 0.890 | Ens v2 ANYx2+USleepCSDP+LGBM (E19) 0.904 |
| N3 | **Ens v2 +bias** (E19b) | 0.833 | 0.830 | 0.836 | Ens v2 ANYx2+USleepCSDP+LGBM (E19) 0.833 | LightGBM (ours) (E00) 0.873 |
| REM | **Ens v2 ANYx2+USleepCSDP+LGBM** (E19) | 0.915 | 0.915 | 0.915 | Ens v2 +bias (E19b) 0.915 | Ens v2 +bias (E19b) 0.918 |

## SC

| Class | Champion | F1 | Recall | Precision | Runner-up | Best recall model |
|---|---|---|---|---|---|---|
| Wake | **Ens 0.7ANY+0.3RSN+bias** (E16) | 0.986 | 0.983 | 0.990 | AnySleep 3ch (E11) 0.986 | YASA crop (E02c) 0.994 |
| N1 | **Ens v2 +bias** (E19b) | 0.620 | 0.691 | 0.562 | Ens v2 ANYx2+USleepCSDP+LGBM (E19) 0.619 | Ens v2 +bias (E19b) 0.691 |
| N2 | **Ens v2 ANYx2+USleepCSDP+LGBM** (E19) | 0.888 | 0.903 | 0.874 | U-Sleep CSDP (open) (E21) 0.886 | U-Sleep CSDP (open) (E21) 0.912 |
| N3 | **Ens v2 +bias** (E19b) | 0.822 | 0.793 | 0.853 | Ens v2 ANYx2+USleepCSDP+LGBM (E19) 0.822 | LightGBM (ours) (E00) 0.865 |
| REM | **U-Sleep CSDP (open)** (E21) | 0.919 | 0.918 | 0.919 | Ens v2 ANYx2+USleepCSDP+LGBM (E19) 0.909 | U-Sleep CSDP (open) (E21) 0.918 |

## ST

| Class | Champion | F1 | Recall | Precision | Runner-up | Best recall model |
|---|---|---|---|---|---|---|
| Wake | **Ens ANYx3+LGBM** (E17) | 0.920 | 0.912 | 0.929 | Ens ANYx3+LGBM+bias (E18) 0.915 | YASA Pz+EOG (E03) 0.993 |
| N1 | **Ens 0.7ANY+0.3RSN+bias** (E16) | 0.745 | 0.742 | 0.748 | Ens ANYx3+LGBM+bias (E18) 0.739 | Ens 0.7ANY+0.3RSN+bias (E16) 0.742 |
| N2 | **AnySleep 3ch** (E11) | 0.921 | 0.924 | 0.917 | Ens 0.7ANY+0.3RSN+bias (E16) 0.919 | AnySleep 3ch (E11) 0.924 |
| N3 | **AnySleep 3ch** (E11) | 0.873 | 0.893 | 0.854 | Ens 0.7ANY+0.3RSN+bias (E16) 0.869 | Ens v2 ANYx2+USleepCSDP+LGBM (E19) 0.904 |
| REM | **AnySleep 3ch** (E11) | 0.949 | 0.954 | 0.945 | Ens 0.7ANY+0.3RSN+bias (E16) 0.948 | AnySleep 3ch (E11) 0.954 |
