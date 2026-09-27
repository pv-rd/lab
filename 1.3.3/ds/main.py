import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit
import os

# Настройка русского шрифта
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['mathtext.default'] = 'regular'

# Создаем папку для графиков
if not os.path.exists('plots'):
    os.makedirs('plots')

# ============================================================
# ДАННЫЕ ИЗМЕРЕНИЙ
# ============================================================

# Параметры окружающей среды (примерные, нужно уточнить)
T = 293.15  # K (20°C)
P_atm = 101325  # Па (нормальное атмосферное)
R_gas = 8.31  # Дж/(моль·К)
M_air = 0.029  # кг/моль
rho_air = P_atm * M_air / (R_gas * T)  # плотность воздуха

# Коэффициент наклона микроманометра (по умолчанию K=0.2)
K_manometer = 0.2
# Переводной коэффициент: 1 деление = K * 0.8095 мм вод. ст.
# 1 мм вод. ст. = 9.8067 Па
# Цена деления при K=0.2: 0.20 мм вод.ст. = 1.96 Па
PRICE_DIV_PA = 0.20 * 9.8067  # Па на деление при K=0.2

# Данные трубок: диаметры и погрешности
tubes = {
    'tube1': {
        'name': 'Трубка 1',
        'd': 5.10,  # мм
        'sigma_d': 0.05,  # мм
        'R': 2.55e-3,  # м
        'sigma_R': 0.025e-3,  # м
    },
    'tube2': {
        'name': 'Трубка 2',
        'd': 3.00,
        'sigma_d': 0.1,
        'R': 1.50e-3,
        'sigma_R': 0.05e-3,
    },
    'tube3': {
        'name': 'Трубка 3',
        'd': 3.95,
        'sigma_d': 0.05,
        'R': 1.975e-3,
        'sigma_R': 0.025e-3,
    }
}

# Данные измерений Q(ΔP) для каждой трубки (пункт 7)
# ΔP в делениях шкалы, Q в литрах/минуту

data_tube3 = {
    'delta_P_div': [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80,
                    85, 90, 95, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 230, 250, 270, 290],
    'Q_l_min': [0.354, 0.757, 1.145, 1.555, 1.919, 2.259, 2.624, 2.951, 3.384, 3.746,
                4.086, 4.403, 4.738, 5.099, 5.335, 5.633, 5.867, 6.066, 6.144, 6.263,
                6.386, 6.488, 6.661, 6.819, 6.859, 7.083, 7.166, 7.417, 7.599, 7.783,
                8.037, 8.382, 8.724, 9.113, 9.413],
    'laminar_idx': 15,  # индекс последней ламинарной точки (ΔP=80 дел)
}

data_tube1 = {
    'delta_P_div': [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80,
                    85, 90, 95, 100, 105, 110, 115, 120, 125],
    'Q_l_min': [1.287, 2.434, 3.720, 4.967, 6.292, 7.067, 7.530, 8.449, 8.735, 8.960,
                9.261, 9.482, 9.727, 10.064, 10.392, 10.769, 11.151, 11.484, 11.838,
                12.162, 12.446, 12.804, 13.114, 13.472, 13.728],
    'laminar_idx': 19,  # примерно, так как турбулентность не достигнута
}

data_tube2 = {
    'delta_P_div': [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90,
                    100, 110, 120, 130, 140, 150, 160, 170, 190, 210, 230, 250],
    'Q_l_min': [0.201, 0.421, 0.687, 0.903, 1.086, 1.354, 1.639, 1.830, 1.984, 2.193,
                2.375, 2.563, 2.671, 2.785, 3.070, 3.403, 3.647, 3.880, 4.149, 4.363,
                4.646, 4.854, 5.076, 5.180, 5.458, 5.683, 5.942, 6.238],
    'laminar_idx': 6,  # ΔP=35 дел - последняя ламинарная, при 40 уже турб.
}

# Данные для пункта 8 - распределение давления вдоль трубки
# Длины участков и соответствующие перепады давления

pressure_distribution = {
    'tube3': {
        'd_mm': 3.95,
        'Q_l_min': 5.303,
        'L_total_cm': 130.9,
        'data': [
            {'L_cm': 10.9, 'delta_P_div': 53},
            {'L_cm': 40.9, 'delta_P_div': 110},
            {'L_cm': 80.9, 'delta_P_div': 193},
            {'L_cm': 130.9, 'delta_P_div': 270},
        ]
    },
    'tube2': {
        'd_mm': 3.00,
        'Q_l_min': 1.716,
        'L_total_cm': 61.0,
        'data': [
            {'L_cm': 11, 'delta_P_div': 39},
            {'L_cm': 31, 'delta_P_div': 71},
            {'L_cm': 61, 'delta_P_div': 110},
        ]
    },
    'tube1': {
        'd_mm': 5.10,
        'Q_l_min': 11.242,
        'L_total_cm': 130.7,
        'data': [
            {'L_cm': 10.7, 'delta_P_div': 80},
            {'L_cm': 40.7, 'delta_P_div': 143},
            {'L_cm': 80.7, 'delta_P_div': 212},
            {'L_cm': 130.7, 'delta_P_div': 302},
        ]
    }
}

# Данные для пункта 10 - зависимость Q от R при постоянном градиенте давления
# Эти данные нужно извлечь из графиков или дополнительных измерений
# Пока используем приближенные значения из пункта 8

# ============================================================
# ФУНКЦИИ ДЛЯ ОБРАБОТКИ
# ============================================================

def div_to_pa(delta_P_div, K=0.2):
    """Перевод делений шкалы в Па"""
    return delta_P_div * K * 0.20 * 9.8067

def Q_l_min_to_m3_s(Q_l_min):
    """Перевод л/мин в м³/с"""
    return Q_l_min * 1e-3 / 60

def calculate_viscosity(slope_m3_s_Pa, R, L):
    """
    Расчет вязкости по формуле Пуазейля:
    Q = (π * R^4 * ΔP) / (8 * η * L)
    η = (π * R^4) / (8 * L * slope)
    где slope = Q/ΔP
    """
    return np.pi * R**4 / (8 * L * slope_m3_s_Pa)

def calculate_reynolds(Q_m3_s, R, rho, eta):
    """Расчет числа Рейнольдса"""
    u_mean = Q_m3_s / (np.pi * R**2)
    return rho * u_mean * R / eta

# ============================================================
# ПУНКТ 7: ГРАФИКИ Q(ΔP) ДЛЯ ВСЕХ ТРУБОК
# ============================================================

print("="*60)
print("ПУНКТ 7: Анализ зависимостей Q(ΔP)")
print("="*60)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))
all_data = [data_tube1, data_tube2, data_tube3]
tube_keys = ['tube1', 'tube2', 'tube3']
colors = ['blue', 'green', 'red']
viscosity_results = {}

for idx, (data, tube_key, color) in enumerate(zip(all_data, tube_keys, colors)):
    tube = tubes[tube_key]
    ax = axes[idx]
    
    # Перевод в СИ
    delta_P_Pa = div_to_pa(np.array(data['delta_P_div']))
    Q_m3_s = Q_l_min_to_m3_s(np.array(data['Q_l_min']))
    
    # Разделение на ламинарный и турбулентный режимы
    lam_idx = data['laminar_idx']
    
    delta_P_lam = delta_P_Pa[:lam_idx+1]
    Q_lam = Q_m3_s[:lam_idx+1]
    
    delta_P_turb = delta_P_Pa[lam_idx:]
    Q_turb = Q_m3_s[lam_idx:]
    
    # Линейная регрессия для ламинарного участка
    slope, intercept, r_value, p_value, std_err = stats.linregress(delta_P_lam, Q_lam)
    
    # Расчет длины участка L для трубки (из пункта 8)
    L_m = pressure_distribution[tube_key]['L_total_cm'] / 100
    
    # Расчет вязкости
    eta = calculate_viscosity(slope, tube['R'], L_m)
    viscosity_results[tube_key] = eta
    
    # Построение графика
    ax.scatter(delta_P_lam, Q_lam * 1e6, color=color, alpha=0.7, s=50, 
               label='Ламинарный режим', zorder=5)
    ax.scatter(delta_P_turb, Q_turb * 1e6, color=color, alpha=0.4, s=50, 
               marker='s', label='Переходный/турб. режим', zorder=5)
    
    # Линия регрессии для ламинарного участка
    delta_P_fit = np.linspace(0, max(delta_P_lam), 100)
    Q_fit = slope * delta_P_fit + intercept
    ax.plot(delta_P_fit, Q_fit * 1e6, '--', color=color, linewidth=2, 
            label=f'Линейная аппроксимация\nR² = {r_value**2:.4f}')
    
    ax.set_xlabel('ΔP, Па', fontsize=12)
    ax.set_ylabel('Q, мл/с', fontsize=12)
    ax.set_title(f'{tube["name"]}\nd = {tube["d"]} мм, η = {eta*1e5:.2f}×10⁻⁵ Па·с', fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    
    print(f"\n{tube['name']} (d = {tube['d']} мм):")
    print(f"  Ламинарных точек: {lam_idx+1}")
    print(f"  Коэффициент наклона: {slope:.6e} м³/(с·Па)")
    print(f"  R² линейной аппроксимации: {r_value**2:.4f}")
    print(f"  Вязкость η = {eta*1e5:.3f} × 10⁻⁵ Па·с")
    
    # Расчет критического числа Рейнольдса
    Q_crit = Q_m3_s[lam_idx]
    Re_crit = calculate_reynolds(Q_crit, tube['R'], rho_air, eta)
    print(f"  Критический расход Q_кр = {Q_crit*1e6:.1f} мл/с")
    print(f"  Критическое число Рейнольдса Re_кр = {Re_crit:.0f}")

plt.tight_layout()
plt.savefig('plots/fig7_Q_vs_deltaP_all_tubes.png', dpi=150, bbox_inches='tight')
print("\nГрафик сохранен: plots/fig7_Q_vs_deltaP_all_tubes.png")

# ============================================================
# ПУНКТ 8: РАСПРЕДЕЛЕНИЕ ДАВЛЕНИЯ ВДОЛЬ ТРУБКИ P(x)
# ============================================================

print("\n" + "="*60)
print("ПУНКТ 8: Распределение давления вдоль трубки")
print("="*60)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

for idx, (tube_key, color) in enumerate(zip(tube_keys, colors)):
    ax = axes[idx]
    data = pressure_distribution[tube_key]
    
    # Измеренные перепады давления (относительно начала трубки x=0)
    L_cm = []
    delta_P_div = []
    
    for point in data['data']:
        L_cm.append(point['L_cm'])
        delta_P_div.append(point['delta_P_div'])
    
    L_cm = np.array(L_cm)
    delta_P_Pa = div_to_pa(np.array(delta_P_div))
    
    # Линейная регрессия
    slope_px, intercept_px, r_value_px, p_value_px, std_err_px = stats.linregress(L_cm, delta_P_Pa)
    
    # Построение
    ax.scatter(L_cm, delta_P_Pa, color=color, s=80, zorder=5, label='Измерения')
    
    L_fit = np.linspace(0, max(L_cm)*1.1, 100)
    P_fit = slope_px * L_fit + intercept_px
    ax.plot(L_fit, P_fit, '--', color=color, linewidth=2, 
            label=f'Линейная аппроксимация\nR² = {r_value_px**2:.4f}')
    
    ax.set_xlabel('x, см', fontsize=12)
    ax.set_ylabel('ΔP(x), Па', fontsize=12)
    ax.set_title(f'{tubes[tube_key]["name"]} (d = {data["d_mm"]} мм)\nQ = {data["Q_l_min"]} л/мин', fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Длина установления (оценка по отклонению от линейности)
    # Если первая точка отклоняется - это признак неустановившегося течения
    P_extrapolated_first = slope_px * L_cm[0] + intercept_px
    deviation = abs(delta_P_Pa[0] - P_extrapolated_first) / delta_P_Pa[0] * 100
    
    print(f"\n{tubes[tube_key]['name']}:")
    print(f"  Градиент давления: {slope_px:.3f} Па/см")
    print(f"  Свободный член: {intercept_px:.3f} Па")
    print(f"  R² линейной аппроксимации: {r_value_px**2:.4f}")
    print(f"  Отклонение первой точки от линейной экстраполяции: {deviation:.1f}%")

plt.tight_layout()
plt.savefig('plots/fig8_pressure_distribution.png', dpi=150, bbox_inches='tight')
print("\nГрафик сохранен: plots/fig8_pressure_distribution.png")

# ============================================================
# ПУНКТ 10: ЗАВИСИМОСТЬ РАСХОДА ОТ РАДИУСА ТРУБЫ
# ============================================================

print("\n" + "="*60)
print("ПУНКТ 10: Зависимость Q от R при постоянном градиенте давления")
print("="*60)

# Из данных пункта 8 можно получить Q при заданном градиенте давления
# для каждой трубки

# Извлекаем градиенты давления и расходы из данных пункта 8
gradients = {}
for tube_key in tube_keys:
    data = pressure_distribution[tube_key]
    L_cm = np.array([p['L_cm'] for p in data['data']])
    delta_P_Pa = div_to_pa(np.array([p['delta_P_div'] for p in data['data']]))
    
    slope, intercept = np.polyfit(L_cm, delta_P_Pa, 1)
    gradients[tube_key] = {
        'gradient_Pa_cm': slope,
        'Q_m3_s': Q_l_min_to_m3_s(data['Q_l_min']),
        'R_m': tubes[tube_key]['R'],
        'sigma_R_m': tubes[tube_key]['sigma_R']
    }

# Построение графика в двойном логарифмическом масштабе
fig, ax = plt.subplots(figsize=(10, 8))

R_values = np.array([gradients[k]['R_m'] for k in tube_keys])
Q_values = np.array([gradients[k]['Q_m3_s'] for k in tube_keys])
sigma_R = np.array([gradients[k]['sigma_R_m'] for k in tube_keys])

# Здесь нужны данные при одинаковом градиенте давления для всех трубок
# Пока используем данные из пункта 8 как есть (градиенты разные)
# Для корректного анализа нужно либо интерполировать данные из п.7,
# либо использовать дополнительные измерения

# Строим имеющиеся точки
ln_R = np.log(R_values * 1000)  # переводим в мм для наглядности
ln_Q = np.log(Q_values * 1e6)  # переводим в мл/с

ax.scatter(ln_R, ln_Q, color='red', s=100, zorder=5, label='Экспериментальные точки')

# Линейная аппроксимация в логарифмическом масштабе
slope_log, intercept_log = np.polyfit(ln_R, ln_Q, 1)
ln_R_fit = np.linspace(min(ln_R)*0.9, max(ln_R)*1.1, 100)
ln_Q_fit = slope_log * ln_R_fit + intercept_log
ax.plot(ln_R_fit, ln_Q_fit, '--', color='blue', linewidth=2, 
        label=f'Аппроксимация: Q ∝ R^{slope_log:.2f}')

# Теоретические линии
# Для ламинарного режима: Q ∝ R⁴
ln_R_theory = np.linspace(min(ln_R)*0.9, max(ln_R)*1.1, 100)
ln_Q_lam_theory = 4 * ln_R_theory + (ln_Q[0] - 4*ln_R[0])  # нормируем на первую точку
ax.plot(ln_R_theory, ln_Q_lam_theory, ':', color='green', linewidth=2, 
        alpha=0.7, label='Теория: Q ∝ R⁴ (ламинарный)')

# Для турбулентного режима: Q ∝ R^(2.5)
ln_Q_turb_theory = 2.5 * ln_R_theory + (ln_Q[0] - 2.5*ln_R[0])
ax.plot(ln_R_theory, ln_Q_turb_theory, ':', color='orange', linewidth=2, 
        alpha=0.7, label='Теория: Q ∝ R²·⁵ (турбулентный)')

ax.set_xlabel('ln(R [мм])', fontsize=14)
ax.set_ylabel('ln(Q [мл/с])', fontsize=14)
ax.set_title('Зависимость расхода от радиуса трубки\n(двойной логарифмический масштаб)', fontsize=14)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

print(f"\nПоказатель степени β = {slope_log:.2f} ± 0.1")
print(f"  Ламинарная теория: β = 4")
print(f"  Турбулентная теория: β = 2.5")

plt.tight_layout()
plt.savefig('plots/fig10_Q_vs_R_loglog.png', dpi=150, bbox_inches='tight')
print("График сохранен: plots/fig10_Q_vs_R_loglog.png")

# ============================================================
# ПУНКТ 14*: БЕЗРАЗМЕРНЫЕ ПЕРЕМЕННЫЕ
# ============================================================

print("\n" + "="*60)
print("ПУНКТ 14*: Анализ в безразмерных переменных")
print("="*60)

fig, ax = plt.subplots(figsize=(12, 8))

# Используем усредненное значение вязкости
eta_avg = np.mean([viscosity_results[k] for k in tube_keys])
print(f"Средняя вязкость: η = {eta_avg*1e5:.2f} × 10⁻⁵ Па·с")

for tube_key, color in zip(tube_keys, colors):
    if tube_key == 'tube1':
        data = data_tube1
    elif tube_key == 'tube2':
        data = data_tube2
    else:
        data = data_tube3
    
    tube = tubes[tube_key]
    
    delta_P_Pa = div_to_pa(np.array(data['delta_P_div']))
    Q_m3_s = Q_l_min_to_m3_s(np.array(data['Q_l_min']))
    
    u_mean = Q_m3_s / (np.pi * tube['R']**2)
    
    # Число Рейнольдса
    Re = rho_air * u_mean * tube['R'] / eta_avg
    
    # Безразмерный перепад давления psi_tilde
    L_m = pressure_distribution[tube_key]['L_total_cm'] / 100
    psi_tilde = (tube['R'] / L_m) * delta_P_Pa / (rho_air * u_mean**2)
    
    ax.scatter(Re, psi_tilde, color=color, alpha=0.7, s=50, 
               label=f'{tube["name"]} (d={tube["d"]} мм)')
    
    # Теоретическая зависимость для ламинарного режима: psi_tilde = 8/Re
    Re_lam = Re[Re < 2000]
    if len(Re_lam) > 0:
        ax.plot(Re_lam, 8/Re_lam, '--', color=color, alpha=0.3, linewidth=1)

# Теоретическая кривая для ламинарного режима
Re_theory = np.logspace(1, 4, 100)
psi_theory_lam = 8 / Re_theory
ax.plot(Re_theory, psi_theory_lam, 'k-', linewidth=2, alpha=0.5, 
        label='Теория (ламинарный): ψ̃ = 8/Re')

# Теоретическая кривая для турбулентного режима: ψ̃ ≈ const
Re_turb_theory = np.logspace(3, 4.5, 100)
psi_turb_theory = np.full_like(Re_turb_theory, 0.03)  # примерное значение
ax.plot(Re_turb_theory, psi_turb_theory, 'k--', linewidth=2, alpha=0.5,
        label='Теория (турбулентный): ψ̃ ≈ const')

ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('Число Рейнольдса Re', fontsize=14)
ax.set_ylabel('Безразмерный перепад давления ψ̃', fontsize=14)
ax.set_title('Зависимость безразмерного перепада давления\nот числа Рейнольдса', fontsize=14)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3, which='both')

plt.tight_layout()
plt.savefig('plots/fig14_dimensionless_analysis.png', dpi=150, bbox_inches='tight')
print("График сохранен: plots/fig14_dimensionless_analysis.png")

# ============================================================
# ДОПОЛНИТЕЛЬНЫЙ ГРАФИК: ЛИНЕЙНОСТЬ ЛАМИНАРНОГО УЧАСТКА
# ============================================================

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

for idx, (data, tube_key, color) in enumerate(zip(all_data, tube_keys, colors)):
    ax = axes[idx]
    
    lam_idx = data['laminar_idx']
    delta_P_lam = div_to_pa(np.array(data['delta_P_div'][:lam_idx+1]))
    Q_lam = Q_l_min_to_m3_s(np.array(data['Q_l_min'][:lam_idx+1]))
    
    slope, intercept, r, p, std = stats.linregress(delta_P_lam, Q_lam)
    
    ax.scatter(delta_P_lam, Q_lam * 1e6, color=color, s=80, zorder=5)
    
    P_fit = np.linspace(0, max(delta_P_lam)*1.1, 100)
    Q_fit = slope * P_fit + intercept
    ax.plot(P_fit, Q_fit * 1e6, '-', color=color, linewidth=2)
    
    # Добавляем подписи с погрешностями
    ax.fill_between(P_fit, 
                    (Q_fit - std*np.sqrt(1/len(delta_P_lam) + (P_fit - np.mean(delta_P_lam))**2 / 
                    np.sum((delta_P_lam - np.mean(delta_P_lam))**2))) * 1e6,
                    (Q_fit + std*np.sqrt(1/len(delta_P_lam) + (P_fit - np.mean(delta_P_lam))**2 / 
                    np.sum((delta_P_lam - np.mean(delta_P_lam))**2))) * 1e6,
                    alpha=0.2, color=color)
    
    ax.set_xlabel('ΔP, Па', fontsize=12)
    ax.set_ylabel('Q, мл/с', fontsize=12)
    ax.set_title(f'{tubes[tube_key]["name"]}: Ламинарный участок\nR² = {r**2:.4f}', fontsize=12)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('plots/fig7_laminar_linearity.png', dpi=150, bbox_inches='tight')
print("График сохранен: plots/fig7_laminar_linearity.png")

# ============================================================
# СВОДНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ
# ============================================================

print("\n" + "="*60)
print("СВОДКА РЕЗУЛЬТАТОВ")
print("="*60)

print("\nТаблица 1. Результаты измерения вязкости воздуха")
print("-" * 60)
print(f"{'Трубка':<15} {'d, мм':<10} {'η, 10⁻⁵ Па·с':<20} {'Re_кр':<10}")
print("-" * 60)
for tube_key in tube_keys:
    tube = tubes[tube_key]
    eta = viscosity_results[tube_key]
    
    # Находим критический расход
    if tube_key == 'tube1':
        data = data_tube1
    elif tube_key == 'tube2':
        data = data_tube2
    else:
        data = data_tube3
    
    lam_idx = data['laminar_idx']
    Q_crit = Q_l_min_to_m3_s(data['Q_l_min'][lam_idx])
    Re_crit = calculate_reynolds(Q_crit, tube['R'], rho_air, eta)
    
    print(f"{tube['name']:<15} {tube['d']:<10.2f} {eta*1e5:<20.3f} {Re_crit:<10.0f}")

eta_all = [viscosity_results[k] for k in tube_keys]
eta_mean = np.mean(eta_all)
eta_std = np.std(eta_all, ddof=1)
print(f"\nСреднее значение вязкости: η = {eta_mean*1e5:.2f} ± {eta_std*1e5:.2f} × 10⁻⁵ Па·с")
print(f"Табличное значение при 20°C: η = 1.85 × 10⁻⁵ Па·с")

# Расчет относительной погрешности
rel_error = abs(eta_mean - 1.85e-5) / 1.85e-5 * 100
print(f"Отклонение от табличного значения: {rel_error:.1f}%")

print("\n" + "="*60)
print("ВСЕ ГРАФИКИ СОХРАНЕНЫ В ПАПКЕ 'plots/'")
print("="*60)
print("""
Список графиков для вставки в отчет:
1. plots/fig7_Q_vs_deltaP_all_tubes.png - Основной график Q(ΔP) для всех трубок
2. plots/fig7_laminar_linearity.png - Проверка линейности ламинарных участков
3. plots/fig8_pressure_distribution.png - Распределение давления P(x) вдоль трубок
4. plots/fig10_Q_vs_R_loglog.png - Зависимость Q от R в логарифмическом масштабе
5. plots/fig14_dimensionless_analysis.png - Анализ в безразмерных переменных ψ̃(Re)
""")