# Wind Turbine Controller Validation Methodology

## 1. Regulatory & Standards Context
Validation procedures in WindCtrl Validate are aligned with:
- **IEC 61400-1 (ed. 4)**: Wind turbines – Design requirements.
- **IEC 61400-12-1**: Power performance measurements of electricity producing wind turbines.
- **GL Guidelines for the Certification of Wind Turbines (2010)**: Safety system and supervisory controller verification.

## 2. Operational Control Regimes (NREL 5MW Baseline Model)

| Control Region | Wind Range | Primary Objective | Actuator Focus |
|---|---|---|---|
| **Region 1** | $v < 3.0$ m/s | Below cut-in; turbine idling | Blades feathered ($90^\circ$), torque zero |
| **Region 1.5** | $3.0 \le v < 6.0$ m/s | Startup ramp | Blade pitching to fine stop ($0^\circ$), generator accelerating |
| **Region 2** | $6.0 \le v < 11.4$ m/s | Maximum energy capture ($C_p$ tracking) | Blade pitch fixed at fine stop ($0^\circ$), torque follows $T_{gen} = k \cdot \omega_{gen}^2$ |
| **Region 2.5** | $11.4 \le v < 12.0$ m/s | Transition to rated speed | Torque ramps to rated ($43.09$ kNm) |
| **Region 3** | $12.0 \le v \le 25.0$ m/s | Constant rated power regulation ($5,000$ kW) | Collective blade pitch active (PI speed regulation), torque held constant |
| **Cut-out / Shutdown** | $v > 25.0$ m/s or fault | Structural protection shutdown | Collective aerodynamic feathering to $90^\circ$ at up to $8.0^\circ$/s |

## 3. Core Validation Rules & Thresholds

### 3.1 Rotor Speed & Overspeed
- **Operational Ceiling**: $14.50$ RPM. Readings $\le 14.50$ RPM are `PASS`.
- **Advisory Buffer Zone**: $(14.50, 15.00]$ RPM triggers a `WARNING`, indicating pitch controller margin depletion.
- **Hard Safety Trip Line**: $> 15.00$ RPM triggers a `FAIL` verdict. The supervisory state must transition to `FAULT_TRIP` or `EMERGENCY_STOP`.
- **Angular Acceleration**: $|d\omega/dt| \le 1.50$ RPM/s.

### 3.2 Blade Pitch Control
- **Region 3 Shedding**: For wind $> 12.4$ m/s, mean blade pitch must exceed $2.0^\circ$. Blades stuck at $0^\circ$ under high wind trigger a critical `FAIL`.
- **Actuator Slew Rate**: $|d\theta/dt| \le 8.00^\circ$/s.
- **Actuator Delay**: Estimated wind-to-pitch cross-correlation delay must not exceed $1.50$ seconds.

### 3.3 Generator Torque
- **Rated Torque**: $43,093.55$ Nm ($43.09$ kNm).
- **Peak Transient Ceiling**: $47,402.91$ Nm ($110\%$ rated). Values $> 47,402.91$ Nm trigger a `FAIL`.
- **Motoring Prohibition**: During active power generation, torque must not drop below $-50.0$ Nm.
- **Dynamic Spike Limit**: $|dQ/dt| \le 15,000$ Nm/s.

### 3.4 Power Curve
- **Rated Power Setpoint**: $5,000$ kW.
- **Tolerance Band**: Observed binned power across $1$ m/s wind bins must not deviate from reference curve by more than $10.0\%$ of rated capacity ($500$ kW).
- **Generator Overload**: Active power must not exceed $5,500$ kW ($110\%$).

### 3.5 Nacelle Yaw Tracking
- **Peak Error**: $|\gamma| \le 10.0^\circ$.
- **Persistent Misalignment**: $30$-second rolling average $|\bar{\gamma}| \le 6.0^\circ$.
