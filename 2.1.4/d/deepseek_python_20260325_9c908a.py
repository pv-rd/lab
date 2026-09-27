import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# Константы
# ============================================================
alpha = 4.28e-3  # температурный коэффициент сопротивления меди, град^-1
P = 6.268  # мощность нагревателя, Вт

# Коэффициенты пересчёта сопротивления в температуру (по описанию)
# Для установки (2) — калориметр
A_RtoT = 14.377980252039598845
B_RtoT = 39.35514018691588785

# ============================================================
# Функции для обработки данных
# ============================================================

def parse_time(time_str):
    """Преобразование времени из формата 'HH:MM:SS' в секунды"""
    try:
        h, m, s = map(int, time_str.strip().split(':'))
        return h * 3600 + m * 60 + s
    except:
        return np.nan

def resistance_to_temperature(R):
    """Пересчёт сопротивления в температуру (К) по формуле из описания"""
    return A_RtoT * R + B_RtoT

def celsius_to_kelvin(Tc):
    """Пересчёт градусов Цельсия в Кельвины"""
    return Tc + 273.15

def exp_decay(t, T0, Tk, tau):
    """Модель экспоненциального охлаждения: T = (T0 - Tk)*exp(-t/tau) + Tk"""
    return (T0 - Tk) * np.exp(-t / tau) + Tk

def exp_heating(t, P_lambda, Tk, tau):
    """Модель нагревания: T = (P/lambda)*(1 - exp(-t/tau)) + Tk"""
    return P_lambda * (1 - np.exp(-t / tau)) + Tk

# ============================================================
# Загрузка и обработка данных
# ============================================================

# Загрузка данных калориметра
df_cal = pd.read_csv('калориметр.txt', encoding='utf-8')
print(f"Загружено {len(df_cal)} строк из калориметр.txt")

# Обработка времени
df_cal['time_sec'] = df_cal['Time'].apply(parse_time)
start_time = df_cal['time_sec'].min()
df_cal['t'] = df_cal['time_sec'] - start_time

# Пересчёт сопротивления в температуру
df_cal['R'] = df_cal['Value'].astype(float)
df_cal['T_K'] = resistance_to_temperature(df_cal['R'])

# Загрузка данных комнатной температуры
df_room = pd.read_csv('комната.txt', encoding='utf-8')
print(f"Загружено {len(df_room)} строк из комната.txt")

# Обработка времени для комнатной температуры
df_room['time_sec'] = df_room['Time'].apply(parse_time)
df_room['t'] = df_room['time_sec'] - start_time

# Пересчёт комнатной температуры в Кельвины
df_room['Tk_C'] = df_room['Value'].astype(float)
df_room['Tk_K'] = celsius_to_kelvin(df_room['Tk_C'])

# ============================================================
# Определение временных интервалов для каждого этапа эксперимента
# ============================================================

# Время событий (в секундах от старта)
t_start = 0  # 22:35:38

# По time.txt:
# 10:40 -> 22:40 -> от старта: 4 мин 22 с = 262 с
# 10:46 -> 22:46 -> от старта: 10 мин 22 с = 622 с
# 11:06 -> 23:06 -> от старта: 30 мин 22 с = 1822 с
# 11:20 -> 23:20 -> от старта: 44 мин 22 с = 2662 с
# 11:26 -> 23:26 -> от старта: 50 мин 22 с = 3022 с
# 11:31 -> 23:31 -> от старта: 55 мин 22 с = 3322 с
# 11:50 -> 23:50 -> от старта: 74 мин 22 с = 4462 с
# 12:08 -> 00:08 -> от старта: 92 мин 22 с = 5542 с
# 12:18 -> 00:18 -> от старта: 102 мин 22 с = 6142 с
# 12:25 -> 00:25 -> от старта: 109 мин 22 с = 6562 с

t_10_40 = 262
t_10_46 = 622
t_11_06 = 1822
t_11_20 = 2662
t_11_26 = 3022
t_11_31 = 3322
t_11_50 = 4462
t_12_08 = 5542
t_12_18 = 6142
t_12_25 = 6562

# Выделение интервалов
mask_empty_heating = (df_cal['t'] >= t_10_46) & (df_cal['t'] <= t_11_06)
mask_empty_cooling = (df_cal['t'] >= t_11_06) & (df_cal['t'] <= t_11_20)

mask_iron_heating = (df_cal['t'] >= t_11_31) & (df_cal['t'] <= t_11_50)
mask_iron_cooling = (df_cal['t'] >= t_11_50) & (df_cal['t'] <= t_12_08)

mask_al_heating = (df_cal['t'] >= t_12_18) & (df_cal['t'] <= t_12_25)
mask_al_cooling = (df_cal['t'] >= t_12_25) & (df_cal['t'] <= t_12_25 + 900)  # 15 мин охлаждения

# Выделение интервалов комнатной температуры
room_empty = (df_room['t'] >= t_10_46) & (df_room['t'] <= t_11_20)
room_iron = (df_room['t'] >= t_11_31) & (df_room['t'] <= t_12_08)
room_al = (df_room['t'] >= t_12_18) & (df_room['t'] <= t_12_25 + 900)

# ============================================================
# График 1: Комнатная температура
# ============================================================
plt.figure(figsize=(10, 6))
plt.plot(df_room['t'] / 60, df_room['Tk_C'], 'b-', linewidth=1)
plt.xlabel('Время, мин')
plt.ylabel('Температура, °C')
plt.title('Комнатная температура в ходе эксперимента')
plt.grid(True, alpha=0.3)
plt.axvline(x=t_10_46/60, color='gray', linestyle='--', alpha=0.5, label='Начало нагрева (пустой)')
plt.axvline(x=t_11_06/60, color='gray', linestyle='--', alpha=0.5, label='Конец нагрева (пустой)')
plt.axvline(x=t_11_31/60, color='gray', linestyle='--', alpha=0.5, label='Начало нагрева (Fe)')
plt.axvline(x=t_11_50/60, color='gray', linestyle='--', alpha=0.5, label='Конец нагрева (Fe)')
plt.axvline(x=t_12_18/60, color='gray', linestyle='--', alpha=0.5, label='Начало нагрева (Al)')
plt.axvline(x=t_12_25/60, color='gray', linestyle='--', alpha=0.5, label='Конец нагрева (Al)')
plt.legend(fontsize=8)
plt.tight_layout()
plt.savefig('room_temp.png', dpi=150)
plt.show()

# ============================================================
# График 2: Все кривые нагревания и охлаждения
# ============================================================
plt.figure(figsize=(12, 8))

# Пустой калориметр
plt.plot(df_cal[mask_empty_heating]['t'] / 60, 
         df_cal[mask_empty_heating]['T_K'], 
         'r-', linewidth=1.5, label='Пустой (нагрев)')
plt.plot(df_cal[mask_empty_cooling]['t'] / 60, 
         df_cal[mask_empty_cooling]['T_K'], 
         'r--', linewidth=1.5, label='Пустой (охлаждение)')

# С железом
plt.plot(df_cal[mask_iron_heating]['t'] / 60, 
         df_cal[mask_iron_heating]['T_K'], 
         'b-', linewidth=1.5, label='С железом (нагрев)')
plt.plot(df_cal[mask_iron_cooling]['t'] / 60, 
         df_cal[mask_iron_cooling]['T_K'], 
         'b--', linewidth=1.5, label='С железом (охлаждение)')

# С алюминием
plt.plot(df_cal[mask_al_heating]['t'] / 60, 
         df_cal[mask_al_heating]['T_K'], 
         'g-', linewidth=1.5, label='С алюминием (нагрев)')
plt.plot(df_cal[mask_al_cooling]['t'] / 60, 
         df_cal[mask_al_cooling]['T_K'], 
         'g--', linewidth=1.5, label='С алюминием (охлаждение)')

plt.xlabel('Время, мин')
plt.ylabel('Температура, К')
plt.title('Кривые нагревания и охлаждения калориметра')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('all_curves.png', dpi=150)
plt.show()

# ============================================================
# График 3: Только кривые нагревания
# ============================================================
plt.figure(figsize=(10, 6))

# Смещение времени для каждого нагрева
t0_empty = t_10_46
t0_iron = t_11_31
t0_al = t_12_18

plt.plot(df_cal[mask_empty_heating]['t'] - t0_empty, 
         df_cal[mask_empty_heating]['T_K'], 
         'r-', linewidth=1.5, label='Пустой калориметр')
plt.plot(df_cal[mask_iron_heating]['t'] - t0_iron, 
         df_cal[mask_iron_heating]['T_K'], 
         'b-', linewidth=1.5, label='С железом')
plt.plot(df_cal[mask_al_heating]['t'] - t0_al, 
         df_cal[mask_al_heating]['T_K'], 
         'g-', linewidth=1.5, label='С алюминием')

plt.xlabel('Время от начала нагрева, с')
plt.ylabel('Температура, К')
plt.title('Кривые нагревания калориметра')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('heating_curves.png', dpi=150)
plt.show()

# ============================================================
# График 4: Спрямлённые кривые охлаждения
# ============================================================

# Функция для обработки кривой охлаждения
def process_cooling_curve(df, mask, t0, name, color):
    """Обработка кривой охлаждения и построение спрямлённого графика"""
    data = df[mask].copy()
    data['t_rel'] = data['t'] - t0
    
    # Усреднённая комнатная температура на интервале
    room_mask = (df_room['t'] >= t0) & (df_room['t'] <= t0 + 900)
    Tk_mean = df_room[room_mask]['Tk_K'].mean()
    
    # Разность температур
    data['dT'] = data['T_K'] - Tk_mean
    data['ln_dT'] = np.log(data['dT'])
    
    # Исключаем начальный нелинейный участок (первые 180 с)
    data_linear = data[data['t_rel'] > 180].copy()
    
    # Линейная аппроксимация
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        data_linear['t_rel'], data_linear['ln_dT'])
    
    print(f"{name}: λ/C = {-slope:.4f} ± {std_err:.4f} с^-1, R² = {r_value**2:.4f}")
    
    # Построение графика
    plt.figure(figsize=(10, 6))
    plt.plot(data['t_rel'], data['ln_dT'], 'o', markersize=2, color=color, alpha=0.5, label='Экспериментальные точки')
    t_fit = np.linspace(180, data['t_rel'].max(), 100)
    plt.plot(t_fit, slope * t_fit + intercept, 'r-', linewidth=2, 
             label=f'Аппроксимация: λ/C = {-slope:.4f} с⁻¹')
    plt.xlabel('Время от начала охлаждения, с')
    plt.ylabel('ln(T - T_k)')
    plt.title(f'Спрямлённая кривая охлаждения: {name}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'cooling_{name.lower()}_linearized.png', dpi=150)
    plt.show()
    
    return -slope, std_err, Tk_mean

# Обработка кривых охлаждения
lamC_empty, err_empty, Tk_empty = process_cooling_curve(df_cal, mask_empty_cooling, t_11_06, 'Empty', 'red')
lamC_iron, err_iron, Tk_iron = process_cooling_curve(df_cal, mask_iron_cooling, t_11_50, 'Iron', 'blue')
lamC_al, err_al, Tk_al = process_cooling_curve(df_cal, mask_al_cooling, t_12_25, 'Aluminum', 'green')

# ============================================================
# График 5: Определение производной в "удобной точке"
# ============================================================

def plot_derivative_analysis(df, mask, t0, name, color, Tk):
    """Анализ производной в точке T = Tk"""
    data = df[mask].copy()
    data['t_rel'] = data['t'] - t0
    
    # Находим момент, когда температура близка к комнатной
    data['T_diff'] = data['T_K'] - Tk
    idx_near = (data['T_diff'] > -0.5) & (data['T_diff'] < 0.5)
    data_near = data[idx_near]
    
    if len(data_near) > 5:
        # Линейная аппроксимация в окрестности
        from scipy import stats
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            data_near['t_rel'], data_near['T_K'])
        
        print(f"{name}: dT/dt = {slope:.4f} ± {std_err:.4f} К/с при T ≈ Tk")
        
        plt.figure(figsize=(10, 6))
        plt.plot(data['t_rel'], data['T_K'], 'o', markersize=2, color=color, alpha=0.5, label='Экспериментальные точки')
        t_fit = np.linspace(data_near['t_rel'].min(), data_near['t_rel'].max(), 100)
        plt.plot(t_fit, slope * t_fit + intercept, 'r-', linewidth=2, 
                 label=f'Аппроксимация: dT/dt = {slope:.4f} К/с')
        plt.axhline(y=Tk, color='k', linestyle='--', alpha=0.5, label=f'T_k = {Tk:.2f} К')
        plt.xlabel('Время от начала нагрева, с')
        plt.ylabel('Температура, К')
        plt.title(f'Определение производной в "удобной точке": {name}')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig(f'derivative_{name.lower()}.png', dpi=150)
        plt.show()
        
        return slope, std_err
    else:
        print(f"{name}: Недостаточно точек в окрестности T = Tk")
        return None, None

# Получаем средние комнатные температуры для каждого этапа
Tk_empty = df_room[room_empty]['Tk_K'].mean()
Tk_iron = df_room[room_iron]['Tk_K'].mean()
Tk_al = df_room[room_al]['Tk_K'].mean()

print(f"\nСредние комнатные температуры:")
print(f"Пустой калориметр: {Tk_empty:.2f} К")
print(f"С железом: {Tk_iron:.2f} К")
print(f"С алюминием: {Tk_al:.2f} К")

# Анализ производных
dTdt_empty, err_empty_dt = plot_derivative_analysis(df_cal, mask_empty_heating, t_10_46, 'Empty', 'red', Tk_empty)
dTdt_iron, err_iron_dt = plot_derivative_analysis(df_cal, mask_iron_heating, t_11_31, 'Iron', 'blue', Tk_iron)
dTdt_al, err_al_dt = plot_derivative_analysis(df_cal, mask_al_heating, t_12_18, 'Aluminum', 'green', Tk_al)

# ============================================================
# Расчёт теплоёмкостей
# ============================================================

print("\n" + "="*60)
print("РЕЗУЛЬТАТЫ РАСЧЁТОВ")
print("="*60)

# Интегральный метод
print("\nИнтегральный метод:")
C_cal_int = 1.011 / lamC_empty
C_fe_int = 1.013 / lamC_iron - C_cal_int
C_al_int = 1.012 / lamC_al - C_cal_int

print(f"C_кал = {C_cal_int:.1f} Дж/К")
print(f"C_Fe = {C_fe_int:.1f} Дж/К")
print(f"C_Al = {C_al_int:.1f} Дж/К")
print(f"c_Fe = {C_fe_int / 0.8148:.1f} Дж/(кг·К)")
print(f"c_Al = {C_al_int / 0.2941:.1f} Дж/(кг·К)")

# Дифференциальный метод
print("\nДифференциальный метод:")
if dTdt_empty is not None:
    C_cal_diff = P / dTdt_empty
    print(f"C_кал = {C_cal_diff:.1f} Дж/К")
if dTdt_iron is not None:
    C_fe_diff = P / dTdt_iron - C_cal_diff
    print(f"C_Fe = {C_fe_diff:.1f} Дж/К")
    print(f"c_Fe = {C_fe_diff / 0.8148:.1f} Дж/(кг·К)")
if dTdt_al is not None:
    C_al_diff = P / dTdt_al - C_cal_diff
    print(f"C_Al = {C_al_diff:.1f} Дж/К")
    print(f"c_Al = {C_al_diff / 0.2941:.1f} Дж/(кг·К)")

print("\n" + "="*60)
print("Табличные значения:")
print("c_Fe = 450 Дж/(кг·К)")
print("c_Al = 900 Дж/(кг·К)")
print("="*60)